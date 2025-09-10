from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path

from aipg.constants import PACKAGE_PATH
from aipg.prompting.utils import (
    parse_and_check_json,
    parse_define_topics,
    parse_llm_ranker_scores,
    parse_project_markdown,
    parse_project_validator_yaml,
)


class PromptGenerator(ABC):
    fields: list[str] = []

    def __init__(self):
        self.parser = self.create_parser()

    @property
    def system_prompt(self):
        return ""

    @abstractmethod
    def generate_prompt(self) -> str:
        pass

    def load_from_file(self, file_path: str | Path) -> str:
        file_path = Path(file_path)
        return file_path.read_text()

    def get_field_parsing_prompt(self) -> str:
        return (
            f"Based on the above information, provide the correct values for the following fields strictly "
            f"in valid JSON format: {', '.join(self.fields)}.\n\n"
            "Important:\n"
            "1. Return only valid JSON. No extra explanations, text, or comments.\n"
            "2. Ensure that the output can be parsed by a JSON parser directly.\n"
            "3. Do not include any non-JSON text or formatting outside the JSON object.\n"
            '4. An example is \\{"<provided_field>": "<correct_value_for_the_field>"\\}\n'
        )

    def generate_chat_prompt(self):
        chat_prompt = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.generate_prompt()},
        ]

        return chat_prompt

    def create_parser(self):
        return partial(parse_and_check_json, expected_keys=self.fields)


class ProjectGenerationPromptGenerator(PromptGenerator):
    def __init__(self, topic: str):
        self.topic = topic
        super().__init__()

    @property
    def system_prompt(self):
        return self.load_from_file(
            Path(PACKAGE_PATH) / "prompting" / "project_generator.md"
        )

    def generate_prompt(self) -> str:
        return f"""[Тема]: {self.topic}"""

    def create_parser(self):
        return parse_project_markdown


class DefineTopicsPromptGenerator(PromptGenerator):
    def __init__(self, comments: list[str]):
        self.comments = comments
        super().__init__()

    @property
    def system_prompt(self):
        return self.load_from_file(
            Path(PACKAGE_PATH) / "prompting" / "define_topics.md"
        )

    def generate_prompt(self) -> str:
        return f"""[Комментарии ревьюера]:{"".join(f"\n- {comment}" for comment in self.comments)}"""

    def create_parser(self):
        return parse_define_topics


class FeedbackPromptGenerator(PromptGenerator):
    def __init__(
        self,
        user_solution: str,
        project_goal: str,
        project_description: str,
        project_input: str,
        project_output: str,
    ):
        self.user_solution = user_solution
        self.project_goal = project_goal
        self.project_description = project_description
        self.project_input = project_input
        self.project_output = project_output
        super().__init__()

    @property
    def system_prompt(self):
        return self.load_from_file(Path(PACKAGE_PATH) / "prompting" / "feedback.md")

    def generate_prompt(self) -> str:
        return (
            f"[Код студента]:\n<student_solution>\n{self.user_solution}\n</student_solution>\n\n"
            "--------------------------------\n\n"
            "Дополнительная информация о задании:\n\n===CONFIDENTIAL===\n\n"
            f"[Цель задания]:\n<project_goal>\n{self.project_goal}\n</project_goal>\n"
            f"[Описание задания]:\n<project_description>\n{self.project_description}\n</project_description>\n"
            f"[Входные данные]:\n<project_input>\n{self.project_input}\n</project_input>\n"
            f"[Ожидаемый результат]:\n<project_output>\n{self.project_output}\n</project_output>\n"
        )

    def create_parser(self):
        # Feedback should return plain text, not JSON
        return lambda text, **kwargs: text.strip()


class LLMRankerPromptGenerator(PromptGenerator):
    def __init__(self, topic: str, candidates: list[str]):
        self.topic = topic
        self.candidates = candidates
        super().__init__()

    @property
    def system_prompt(self):
        return self.load_from_file(Path(PACKAGE_PATH) / "prompting" / "llm_ranker.md")

    def generate_prompt(self) -> str:
        numbered_candidates = "\n".join(
            [f"{i + 1}. {candidate}" for i, candidate in enumerate(self.candidates)]
        )
        return (
            f"[Проблема студента]: {self.topic}"
            "[Похожие проблемы]:\n"
            f"{numbered_candidates}"
        )

    def create_parser(self):
        return parse_llm_ranker_scores


class ProjectValidatorPromptGenerator(PromptGenerator):
    def __init__(self, project_markdown: str):
        self.project_markdown = project_markdown
        super().__init__()

    @property
    def system_prompt(self):
        return self.load_from_file(
            Path(PACKAGE_PATH) / "prompting" / "project_validator.md"
        )

    def generate_prompt(self) -> str:
        return f"[Микропроект для проверки]:\n\n---\n\n{self.project_markdown}\n\n---"

    def create_parser(self):
        return parse_project_validator_yaml


class ProjectCorrectorPromptGenerator(PromptGenerator):
    def __init__(self, source_project: str, validation_report: str):
        self.source_project = source_project
        self.validation_report = validation_report
        super().__init__()

    @property
    def system_prompt(self):
        return self.load_from_file(
            Path(PACKAGE_PATH) / "prompting" / "project_corrector.md"
        )

    def generate_prompt(self) -> str:
        return (
            f"[Исходный микропроект]:\n\n---\n\n{self.source_project}\n\n---\n\n"
            f"[Отчет валидатора]:\n\n---\n\n{self.validation_report}\n\n---"
        )

    def create_parser(self):
        return parse_project_markdown
