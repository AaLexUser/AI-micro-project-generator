import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Annotated, List, Optional

import typer
from rich import print as rprint


@dataclass
class TimingContext:
    start_time: float
    total_time_limit: float

    @property
    def time_elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def time_remaining(self) -> float:
        return self.total_time_limit - self.time_elapsed


@contextmanager
def time_block(description: str, timer: TimingContext):
    """Context manager for timing code blocks and logging the duration."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logging.info(
            f"It took {duration:.2f} seconds {description}. "
            f"Time remaining: {timer.time_remaining:.2f}/{timer.total_time_limit:.2f}"
        )


def run_assistant(
    issue: Annotated[str, typer.Argument(help="Issue description")],
    presets: Annotated[
        Optional[str],
        typer.Option("--presets", "-p", help="Presets"),
    ] = None,
    config_path: Annotated[
        Optional[str],
        typer.Option(
            "--config-path", "-c", help="Path to the configuration file (config.yaml)"
        ),
    ] = None,
    config_overrides: Annotated[
        Optional[List[str]],
        typer.Option(
            "--config_overrides",
            "-o",
            help="Override config values. Format: key=value or key.nested=value. Can be used multiple times.",
        ),
    ] = None,
):
    start_time = time.time()

    logging.info("Starting Cherry AI Project Generator")
    # Load config with all overrides
    try:
        # Local imports to avoid heavy dependencies at package import time
        from aipg.configs.app_config import AppConfig
        from aipg.configs.loader import load_config

        config = load_config(presets, config_path, config_overrides, AppConfig)
        logging.info("Successfully loaded config")
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise

    timer = TimingContext(start_time=start_time, total_time_limit=config.time_limit)

    with time_block("initializing components", timer):
        rprint("🤖 [bold red] Welcome to Cherry AI Project Generator [/bold red]")
        from aipg.assistant import Assistant
        from aipg.task import Task

        assistant = Assistant(config)
        task = Task(issue_description=issue)
        task = assistant.generate_project(task)
        rprint(task)


def main():
    app = typer.Typer()
    app.command()(run_assistant)
    app()


if __name__ == "__main__":
    main()
