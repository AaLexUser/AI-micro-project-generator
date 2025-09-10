import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Annotated, List, Optional

import typer
from rich import print as rprint

from aipg.assistant import ProjectAssistant
from aipg.configs.app_config import AppConfig
from aipg.configs.loader import load_config
from aipg.state import ProjectAgentState


@dataclass
class TimingContext:
    start_time: float
    total_time_limit: float

    @property
    def time_elapsed(self) -> float:
        # Monotonic for robust duration measurement
        return time.perf_counter() - self.start_time

    @property
    def time_remaining(self) -> float:
        # Never show negative remaining time in logs
        return max(0.0, self.total_time_limit - self.time_elapsed)


@contextmanager
def time_block(description: str, timer: TimingContext):
    """Context manager for timing code blocks and logging the duration."""
    start_time = time.perf_counter()
    try:
        yield
    except Exception:
        logging.exception(f"Failure while {description}")
        raise
    finally:
        duration = time.perf_counter() - start_time
        logging.info(
            f"It took {duration:.2f} seconds {description}. "
            f"Time remaining: {timer.time_remaining:.2f}/{timer.total_time_limit:.2f}"
        )


def run_assistant(
    comments: Annotated[List[str], typer.Argument(help="List of topic descriptions")],
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
    start_time = time.perf_counter()

    logging.info("Starting Cherry AI Project Generator")
    # Load config with all overrides
    try:
        config = load_config(presets, config_path, config_overrides, AppConfig)
        logging.info("Successfully loaded config")
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise

    time_limit = getattr(config, "time_limit", float("inf")) or float("inf")
    timer = TimingContext(start_time=start_time, total_time_limit=float(time_limit))

    with time_block("initializing components", timer):
        rprint("🤖 [bold red] Welcome to Cherry AI Project Generator [/bold red]")
        assistant = ProjectAssistant(config)
        state = ProjectAgentState(comments=comments)
        state = assistant.execute(state)
        rprint(state)
    return state


def main():
    app = typer.Typer()
    app.command()(run_assistant)
    app()


if __name__ == "__main__":
    main()
