import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel

from aipg.domain import (
    FeedbackAgentState,
    ProcessTopicAgentState,
    ProjectsAgentState,
)
from aipg.exceptions import OutputParserException
from aipg.llm import LLMClient
from aipg.prompting.prompt_generator import (
    BugFixerPromptGenerator,
    DefineTopicsPromptGenerator,
    FeedbackPromptGenerator,
    LLMRankerPromptGenerator,
    ProjectCorrectorPromptGenerator,
    ProjectGenerationPromptGenerator,
    ProjectValidatorPromptGenerator,
    PromptGenerator,
)
from aipg.prompting.utils import format_project_validation_result_yaml
from aipg.rag.service import RagService
from aipg.sandbox.domain import SandboxResult
from aipg.sandbox.service import PythonSandboxService

StateT = TypeVar("StateT", bound=BaseModel)

logger = logging.getLogger(__name__)


class TaskInference(Generic[StateT]):
    def __init__(self, llm: LLMClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm: LLMClient = llm
        self.fallback_value: Optional[str] = None
        self.ignored_value: List[str] = []

    def initialize_task(self, state: StateT):
        self.prompt_generator: Optional[PromptGenerator] = None
        self.valid_values = None

    def log_value(self, key: str, value: Any, max_width: int = 1600) -> None:
        """Logs a key-value pair with formatted output"""
        if value is None:
            logger.warning("Failed to identify %s; setting to None.", key)
            return

        prefix = key
        value_str = str(value).replace("\n", "\\n")
        if len(prefix) + len(value_str) > max_width:
            value_str = value_str[: max_width - len(prefix) - 3] + "..."

        bold_start = "\033[1m"
        bold_end = "\033[0m"

        logger.info(f"{bold_start}{prefix}{bold_end}: {value_str}")

    async def transform(self, state: StateT) -> StateT:
        self.initialize_task(state)
        parser_output = await self._chat_and_parse_prompt_output()
        for k, v in parser_output.items():
            if v in self.ignored_value:
                v = None
            self.log_value(k, v)
            setattr(state, k, self.post_process(state=state, value=v))
        return state

    def post_process(self, state, value):
        return value

    async def _chat_and_parse_prompt_output(self) -> Dict[str, Any]:
        try:
            assert self.prompt_generator is not None, (
                "prompt_generator is not initialized"
            )
            chat_prompt = self.prompt_generator.generate_chat_prompt()
            logger.debug(f"LLM chat_prompt:\n{chat_prompt}")
            output = await self.llm.query(chat_prompt)
            logger.debug(f"LLM output:\n{output}")
            parsed_output = self.prompt_generator.parser(
                output,
                valid_values=self.valid_values,
                fallback_value=self.fallback_value,
            )
            return parsed_output
        except OutputParserException as e:
            logger.error(f"Failed to parse output: {e}")
            raise e


class DefineTopicsInference(TaskInference[ProjectsAgentState]):
    def initialize_task(self, state: ProjectsAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProjectsAgentState) -> ProjectsAgentState:
        self.initialize_task(state)
        comments = state.comments
        self.prompt_generator = DefineTopicsPromptGenerator(comments=comments)
        chat_prompt = self.prompt_generator.generate_chat_prompt()
        last_exception: OutputParserException | None = None
        for attempt in range(1, 4):
            response = await self.llm.query(chat_prompt)
            try:
                topics = self.prompt_generator.parser(response)
                break
            except OutputParserException as e:
                last_exception = e
                chat_prompt.extend(
                    [
                        {"role": "assistant", "content": response or ""},
                        {"role": "user", "content": str(e)},
                    ]
                )
                logger.warning(
                    f"Define topics parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                )
        else:
            logger.error(
                f"Failed to parse define topics after 3 attempts: {last_exception}"
            )
            raise (
                last_exception
                if last_exception
                else OutputParserException(
                    "Define topics parsing failed with no additional context"
                )
            )
        state.topics = topics
        return state


class ProjectGenerationInference(TaskInference[ProcessTopicAgentState]):
    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        if state.project is None:
            self.prompt_generator = ProjectGenerationPromptGenerator(topic=state.topic)
            chat_prompt = self.prompt_generator.generate_chat_prompt()
            last_exception: OutputParserException | None = None
            for attempt in range(1, 4):
                response = await self.llm.query(chat_prompt)
                try:
                    state.project = self.prompt_generator.parser(response)
                    break
                except OutputParserException as e:
                    last_exception = e
                    error_feedback = (
                        f"Ошибка парсинга: {e}\n\n"
                        "ВАЖНО: Ответь ТОЛЬКО чистым markdown без дополнительных объяснений или комментариев. "
                        "Начни сразу с заголовка '# Микропроект для углубления темы: ...' "
                        "Не добавляй никакого текста до или после markdown контента."
                    )
                    chat_prompt.extend(
                        [
                            {"role": "assistant", "content": response or ""},
                            {"role": "user", "content": error_feedback},
                        ]
                    )
                    logger.warning(
                        f"Project parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                    )
            else:
                logger.error(
                    f"Failed to parse project after 3 attempts: {last_exception}"
                )
                raise (
                    last_exception
                    if last_exception
                    else OutputParserException(
                        "Project parsing failed with no additional context"
                    )
                )
        return state


class FeedbackInference(TaskInference[FeedbackAgentState]):
    def initialize_task(self, state: FeedbackAgentState):
        super().initialize_task(state)

    async def transform(self, state: FeedbackAgentState) -> FeedbackAgentState:
        self.initialize_task(state)
        self.prompt_generator = FeedbackPromptGenerator(
            user_solution=state.user_solution,
            project_goal=state.project.goal,
            project_description=state.project.description,
            project_input=state.project.input_data,
            project_output=state.project.expected_output,
            project_autotest=state.project.autotest,
            execution_result=state.execution_result,
        )
        chat_prompt = self.prompt_generator.generate_chat_prompt()
        response = await self.llm.query(chat_prompt)
        feedback = self.prompt_generator.parser(response)
        state.feedback = feedback
        return state


class LLMRankerInference(TaskInference[ProcessTopicAgentState]):
    def __init__(
        self, llm: LLMClient, similarity_threshold: float = 0.7, *args, **kwargs
    ):
        super().__init__(llm, *args, **kwargs)
        self.similarity_threshold = similarity_threshold

    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        # Extract topic strings from Topic2Project objects
        candidate_topics = [candidate.topic for candidate in state.candidates]

        # Early return if no candidates to avoid unnecessary LLM calls
        if not candidate_topics:
            logger.info(
                f"No candidates found for topic: '{state.topic}', skipping LLM ranking"
            )
            return state

        logger.info(
            f"LLM Ranking initiated for topic: '{state.topic}' with {len(candidate_topics)} candidates"
        )
        logger.debug(f"Candidate topics: {candidate_topics}")

        self.prompt_generator = LLMRankerPromptGenerator(
            topic=state.topic, candidates=candidate_topics
        )
        chat_prompt = self.prompt_generator.generate_chat_prompt()
        last_exception: OutputParserException | None = None
        for attempt in range(1, 4):
            logger.debug(f"LLM Ranking attempt {attempt}/3 for topic '{state.topic}'")
            response = await self.llm.query(chat_prompt)
            try:
                scores = self.prompt_generator.parser(response)
                logger.debug(f"Parsed scores: {scores}")

                # Ensure we have the right number of scores
                if len(scores) != len(state.candidates):
                    raise OutputParserException(
                        f"Expected {len(state.candidates)} scores, got {len(scores)}"
                    )

                # Find the candidate with the highest score
                if scores:  # Only proceed if we have scores
                    best_score_idx = max(range(len(scores)), key=lambda i: scores[i])
                    best_score = scores[best_score_idx]
                    best_topic = state.candidates[best_score_idx].topic

                    logger.info(
                        f"Score analysis for topic '{state.topic}': best candidate '{best_topic}' with score {best_score:.3f}"
                    )

                    # Only set best_candidate if score is above threshold
                    if best_score >= self.similarity_threshold:
                        state.project = state.candidates[best_score_idx].project
                        state.topic = state.candidates[best_score_idx].topic
                        logger.info(
                            f"LLM Ranking successful: selected '{best_topic}' with score {best_score:.3f} (threshold: {self.similarity_threshold})"
                        )
                    else:
                        state.project = None
                        logger.info(
                            f"LLM Ranking completed: no candidate meets threshold. Best score: {best_score:.3f} (threshold: {self.similarity_threshold})"
                        )
                else:
                    # No scores available, no best candidate
                    state.project = None
                    logger.info(
                        "LLM Ranking completed: no scores available, no best candidate selected"
                    )
                break
            except OutputParserException as e:
                last_exception = e
                error_feedback = (
                    f"Parsing error: {e}\n\n"
                    "IMPORTANT: Return ONLY a valid JSON array of floats between 0.0 and 1.0. "
                    f"Expected {len(state.candidates)} scores for {len(state.candidates)} candidates. "
                    "Example: [0.8, 0.2, 0.9]"
                )
                chat_prompt.extend(
                    [
                        {"role": "assistant", "content": response or ""},
                        {"role": "user", "content": error_feedback},
                    ]
                )
                logger.warning(
                    f"LLM ranker parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                )
        else:
            logger.error(
                f"Failed to parse LLM ranker scores after 3 attempts: {last_exception}"
            )
            raise (
                last_exception
                if last_exception
                else OutputParserException(
                    "LLM ranker parsing failed with no additional context"
                )
            )
        return state


class RAGServiceInference(TaskInference[ProcessTopicAgentState]):
    def __init__(self, llm: LLMClient, rag_service: RagService, *args, **kwargs):
        super().__init__(llm, *args, **kwargs)
        self.rag_service = rag_service

    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        # Search for candidates using the RAG service
        logger.info(f"RAG Service Inference initiated for topic: '{state.topic}'")
        candidates = await self.rag_service.try_to_get(state.topic)
        state.candidates = candidates
        logger.info(
            f"RAG Service Inference completed: found {len(candidates)} candidates for topic '{state.topic}'"
        )
        return state


class ProjectValidatorInference(TaskInference[ProcessTopicAgentState]):
    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        if state.project is None:
            logger.warning("No project available for validation")
            return state

        self.prompt_generator = ProjectValidatorPromptGenerator(
            project_markdown=state.project.raw_markdown
        )
        chat_prompt = self.prompt_generator.generate_chat_prompt()
        last_exception: OutputParserException | None = None
        for attempt in range(1, 4):
            response = await self.llm.query(chat_prompt)
            try:
                validation_result = self.prompt_generator.parser(response)
                state.validation_result = validation_result
                break
            except OutputParserException as e:
                last_exception = e
                error_feedback = (
                    f"Parsing error: {e}\n\n"
                    "IMPORTANT: Return ONLY valid YAML with 'is_valid' and 'checks' fields. "
                    "Example:\n"
                    "is_valid: true\n"
                    "checks:\n"
                    "  - rule_id: 'SOLVABILITY'\n"
                    "    passed: true\n"
                    "    comment: 'OK'\n"
                    "  - rule_id: 'AUTOTEST_SCOPE'\n"
                    "    passed: true\n"
                    "    comment: 'OK'"
                )
                chat_prompt.extend(
                    [
                        {"role": "assistant", "content": response or ""},
                        {"role": "user", "content": error_feedback},
                    ]
                )
                logger.warning(
                    f"Project validator parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                )
        else:
            logger.error(
                f"Failed to parse project validator response after 3 attempts: {last_exception}"
            )
            raise (
                last_exception
                if last_exception
                else OutputParserException(
                    "Project validator parsing failed with no additional context"
                )
            )
        return state


class ProjectCorrectorInference(TaskInference[ProcessTopicAgentState]):
    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        if state.project is None or state.validation_result is None:
            logger.warning("No project or validation result available for correction")
            return state

        # Prepare a YAML report from validation_result for the corrector LLM
        validation_report = format_project_validation_result_yaml(
            state.validation_result
        )

        self.prompt_generator = ProjectCorrectorPromptGenerator(
            source_project=state.project.raw_markdown,
            validation_report=validation_report,
        )
        chat_prompt = self.prompt_generator.generate_chat_prompt()
        last_exception: OutputParserException | None = None
        for attempt in range(1, 4):
            response = await self.llm.query(chat_prompt)
            try:
                corrected_project = self.prompt_generator.parser(response)
                state.project = corrected_project
                break
            except OutputParserException as e:
                last_exception = e
                error_feedback = (
                    f"Parsing error: {e}\n\n"
                    "IMPORTANT: Return ONLY the corrected project markdown without any additional explanations, "
                    "comments, or code blocks. Start directly with '# Микропроект для углубления темы:' "
                    "and provide the complete corrected project in the same format as the original."
                )
                chat_prompt.extend(
                    [
                        {"role": "assistant", "content": response or ""},
                        {"role": "user", "content": error_feedback},
                    ]
                )
                logger.warning(
                    f"Project corrector parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                )
        else:
            logger.error(
                f"Failed to parse project corrector response after 3 attempts: {last_exception}"
            )
            raise (
                last_exception
                if last_exception
                else OutputParserException(
                    "Project corrector parsing failed with no additional context"
                )
            )
        return state


class CheckAutotestSandboxInference(TaskInference[ProcessTopicAgentState]):
    def __init__(
        self, llm: LLMClient, sandbox_service: PythonSandboxService, *args, **kwargs
    ):
        super().__init__(llm, *args, **kwargs)
        self.sandbox_service = sandbox_service

    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        if state.project is not None:
            # Ensure autotest contains the placeholder for student solution
            if "{STUDENT_SOLUTION}" not in state.project.autotest:
                state.execution_result = SandboxResult(
                    stdout="",
                    stderr="{STUDENT_SOLUTION} должен присутствовать в Автотесте. Проверь его и попробуй снова.",
                    exit_code=1,
                    timed_out=False,
                )
                return state
            code = state.project.autotest.replace(
                "{STUDENT_SOLUTION}", state.project.expert_solution
            )
            result = await self.sandbox_service.run_code(code)
            state.execution_result = result
        return state


class BugFixerInference(TaskInference[ProcessTopicAgentState]):
    def initialize_task(self, state: ProcessTopicAgentState):
        super().initialize_task(state)

    async def transform(self, state: ProcessTopicAgentState) -> ProcessTopicAgentState:
        self.initialize_task(state)
        if state.project is None or state.execution_result is None:
            logger.warning("No project or execution result available for bug fixing")
            return state

        # Check if there are any errors to fix
        if (
            state.execution_result.exit_code == 0
            and not state.execution_result.timed_out
        ):
            logger.info("No errors detected in execution result, skipping bug fixing")
            return state

        logger.info("Bug fixing initiated for project with execution errors")
        logger.debug(
            f"Execution result: exit_code={state.execution_result.exit_code}, "
            f"timed_out={state.execution_result.timed_out}, "
            f"stderr={state.execution_result.stderr}"
        )

        self.prompt_generator = BugFixerPromptGenerator(
            project_markdown=state.project.raw_markdown,
            sandbox_result=state.execution_result,
        )
        chat_prompt = self.prompt_generator.generate_chat_prompt()
        last_exception: OutputParserException | None = None
        for attempt in range(1, 4):
            response = await self.llm.query(chat_prompt)
            try:
                fixed_project = self.prompt_generator.parser(response)
                state.project = fixed_project
                logger.info("Bug fixing completed successfully")
                break
            except OutputParserException as e:
                last_exception = e
                error_feedback = (
                    f"Parsing error: {e}\n\n"
                    "IMPORTANT: Return ONLY the corrected project markdown without any additional explanations, "
                    "comments, or code blocks. Start directly with '# Микропроект для углубления темы:' "
                    "and provide the complete corrected project in the same format as the original."
                )
                chat_prompt.extend(
                    [
                        {"role": "assistant", "content": response or ""},
                        {"role": "user", "content": error_feedback},
                    ]
                )
                logger.warning(
                    f"Bug fixer parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                )
        else:
            logger.error(
                f"Failed to parse bug fixer response after 3 attempts: {last_exception}"
            )
            raise (
                last_exception
                if last_exception
                else OutputParserException(
                    "Bug fixer parsing failed with no additional context"
                )
            )
        return state


class CheckUserSolutionSandboxInference(TaskInference[FeedbackAgentState]):
    def __init__(
        self, llm: LLMClient, sandbox_service: PythonSandboxService, *args, **kwargs
    ):
        super().__init__(llm, *args, **kwargs)
        self.sandbox_service = sandbox_service

    def initialize_task(self, state: FeedbackAgentState):
        super().initialize_task(state)

    async def transform(self, state: FeedbackAgentState) -> FeedbackAgentState:
        self.initialize_task(state)
        if state.project is not None:
            code = state.project.autotest.replace(
                "{STUDENT_SOLUTION}", state.user_solution
            )
            result = await self.sandbox_service.run_code(code)
            state.execution_result = result
        return state
