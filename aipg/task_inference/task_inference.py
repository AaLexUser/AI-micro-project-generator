import logging
from typing import Any, Dict, List, Optional

from aipg.exceptions import OutputParserException
from aipg.llm import LLMClient
from aipg.prompting.prompt_generator import (
    ProjectGenerationPromptGenerator,
    PromptGenerator,
)
from aipg.state import AgentState

logger = logging.getLogger(__name__)


class TaskInference:
    def __init__(self, llm: LLMClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm: LLMClient = llm
        self.fallback_value: Optional[str] = None
        self.ignored_value: List[str] = []

    def initialize_task(self, state: AgentState):
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

    def transform(self, state: AgentState) -> AgentState:
        self.initialize_task(state)
        parser_output = self._chat_and_parse_prompt_output()
        for k, v in parser_output.items():
            if v in self.ignored_value:
                v = None
            self.log_value(k, v)
            setattr(state, k, self.post_process(state=state, value=v))
        return state

    def post_process(self, state, value):
        return value

    def _chat_and_parse_prompt_output(self) -> Dict[str, Optional[str]]:
        try:
            assert self.prompt_generator is not None, (
                "prompt_generator is not initialized"
            )
            chat_prompt = self.prompt_generator.generate_chat_prompt()
            logger.debug(f"LLM chat_prompt:\n{chat_prompt}")
            output = self.llm.query(chat_prompt)
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


class ProjectGenerationInference(TaskInference):
    def initialize_task(self, state: AgentState):
        super().initialize_task(state)
    
    def transform(self, state: AgentState) -> AgentState:
        self.initialize_task(state)
        topic2project = state.topic2project
        for item in state.topic2project:
            if item.project is None:
                self.prompt_generator = ProjectGenerationPromptGenerator(
                    topic=item.topic
                )
                chat_prompt = self.prompt_generator.generate_chat_prompt()
                last_exception: OutputParserException | None = None
                for attempt in range(1, 4):
                    response = self.llm.query(chat_prompt)
                    try:
                        item.project = self.prompt_generator.parser(response)
                        break
                    except OutputParserException as e:
                        last_exception = e
                        chat_prompt.extend([
                            {"role": "assistant", "content": response or ""},
                            {"role": "user", "content": str(e)},
                        ])
                        logger.warning(
                            f"Project parse failed on attempt {attempt}/3; adding error to context and retrying: {e}"
                        )
                else:
                    logger.error(
                        f"Failed to parse project after 3 attempts: {last_exception}"
                    )
                    raise last_exception if last_exception else OutputParserException(
                        "Project parsing failed with no additional context"
                    )
        state.topic2project = topic2project
        return state
