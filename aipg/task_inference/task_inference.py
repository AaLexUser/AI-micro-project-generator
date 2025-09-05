import logging
from typing import Any, Dict, List, Optional

from aipg.exceptions import OutputParserException
from aipg.llm import LLMClient
from aipg.prompting.prompt_generator import (
    MicroTaskGenerationPromptGenerator,
    PromptGenerator,
)
from aipg.task import Task

logger = logging.getLogger(__name__)


class TaskInference:
    def __init__(self, llm: LLMClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm: LLMClient = llm
        self.fallback_value: Optional[str] = None
        self.ignored_value: List[str] = []

    def initialize_task(self, task: Task):
        self.prompt_genetator: Optional[PromptGenerator] = None
        self.valid_values = None

    def log_value(self, key: str, value: Any, max_width: int = 1600) -> None:
        """Logs a key-value pair with formatted output"""
        if not value:
            logger.info(
                f"WARMING: Failed to identify the {key} of the task, it is set to None."
            )
            return

        prefix = key
        value_str = str(value).replace("\n", "\\n")
        if len(prefix) + len(value_str) > max_width:
            value_str = value_str[: max_width - len(prefix) - 3] + "..."

        bold_start = "\033[1m"
        bold_end = "\033[0m"

        logger.info(f"{bold_start}{prefix}{bold_end}: {value_str}")

    def transform(self, task: Task) -> Task:
        self.initialize_task(task)
        parser_output = self._chat_and_parse_prompt_output()
        for k, v in parser_output.items():
            if v in self.ignored_value:
                v = None
            self.log_value(k, v)
            setattr(task, k, self.post_process(task=task, value=v))
        return task

    def post_process(self, task, value):
        return value

    def _chat_and_parse_prompt_output(self) -> Dict[str, Optional[str]]:
        try:
            assert self.prompt_genetator is not None, (
                "prompt_generator is not initialized"
            )
            chat_prompt = self.prompt_genetator.generate_chat_prompt()
            logger.debug(f"LLM chat_prompt:\n{chat_prompt}")
            output = self.llm.query(chat_prompt)
            logger.debug(f"LLM output:\n{output}")
            parsed_output = self.prompt_genetator.parser(
                output,
                valid_values=self.valid_values,
                fallback_value=self.fallback_value,
            )
            return parsed_output
        except OutputParserException as e:
            logger.error(f"Failed to parse output: {e}")
            raise e


class MicroProjectGenerationInference(TaskInference):
    def initialize_task(self, task: Task):
        super().initialize_task(task)
        self.prompt_genetator = MicroTaskGenerationPromptGenerator(
            issue_description=task.issue.description
        )
