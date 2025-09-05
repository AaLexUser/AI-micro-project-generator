from abc import ABC, abstractmethod
from functools import partial

from aipg.prompting.utils import parse_and_check_json


class PromptGenerator(ABC):
    fields: list[str] = []

    def __init__(self, issue_description: str = ""):
        self.issue_description = issue_description
        self.parser = self.create_parser()

    @property
    def system_prompt(self):
        return "You are an expert teacher who helps students learn from their mistakes."

    @property
    def issue_description_prompt(self):
        return f"# Mistake Description\n{self.issue_description}"

    @abstractmethod
    def generate_prompt(self) -> str:
        pass

    def get_field_parsing_prompt(self) -> str:
        return (
            f"Based on the above information, provide the correct values for the following fields strictly "
            f"in valid JSON format: {', '.join(self.fields)}.\n\n"
            "Important:\n"
            "1. Return only valid JSON. No extra explanations, text, or comments.\n"
            "2. Ensure that the output can be parsed by a JSON parser directly.\n"
            "3. Do not include any non-JSON text or formatting outside the JSON object."
            '4. An example is \\{"<provided_field>": "<correct_value_for_the_field>"\\}'
        )

    def generate_chat_prompt(self):
        chat_prompt = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.generate_prompt()},
        ]

        return chat_prompt

    def create_parser(self):
        return partial(parse_and_check_json, expected_keys=self.fields)


class MicroTaskGenerationPromptGenerator(PromptGenerator):
    fields = ["task_description", "task_goal", "expert_solution"]

    def generate_prompt(self) -> str:
        return (
            f"{self.issue_description_prompt}\n\n"
            "Based on the above information, create a small, "
            "focused learning tasks that specifically address misunderstanding. "
            "Micro-task should target one specific error or misconception. "
            "The task should be concise and clear, and should be easy to understand for a student."
            "Determine:\n"
            "task_description: detailed description of the task without hints.\n\n"
            "task_goal: what is user must achieve to complete the task.\n\n"
            "expert_solution: a detailed expert solution to the task.\n\n"
            f"{self.get_field_parsing_prompt()}"
        )
