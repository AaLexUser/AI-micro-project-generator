from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path

from aipg.constants import PACKAGE_PATH
from aipg.prompting.utils import (
    parse_and_check_json,
    parse_project_markdown,
    parse_define_topics,
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
        return self.load_from_file(Path(PACKAGE_PATH) / "prompting" / "project_gen.md")

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
