"""Langfuse tracing implementation for LLM operations."""

import logging
from typing import Any, Dict, List, Tuple

from langfuse import Langfuse

logger = logging.getLogger(__name__)


class LangfuseTracer:
    """Handles Langfuse tracing for LLM operations."""

    def __init__(self, config):
        """Initialize the Langfuse tracer.

        Args:
            config: Application configuration containing Langfuse settings
        """
        self.config = config
        self._langfuse = None

        if (
            config.langfuse.public_key
            and config.langfuse.secret_key
            and config.langfuse.host
        ):
            import os

            os.environ.setdefault("LANGFUSE_PUBLIC_KEY", config.langfuse.public_key)
            os.environ.setdefault("LANGFUSE_SECRET_KEY", config.langfuse.secret_key)
            os.environ.setdefault("LANGFUSE_HOST", config.langfuse.host)

            try:
                self._langfuse = Langfuse()
            except Exception as e:
                logger.warning("Failed to initialize Langfuse client: %s", e)
                self._langfuse = None

    def is_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._langfuse is not None

    def normalize_messages(
        self, messages: str | List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize messages to a consistent chat message list format."""
        return (
            [{"role": "user", "content": messages}]
            if isinstance(messages, str)
            else messages
        )

    def create_litellm_trace(
        self,
        normalized_messages: List[Dict[str, Any]],
        completion_params: Dict[str, Any],
    ) -> Tuple[Any, Any]:
        """Create Langfuse trace and generation for LiteLLM calls."""
        if not self.is_enabled():
            return None, None

        try:
            # Create root trace
            trace = self._langfuse.trace(
                name="litellm_llm_call",
                user_id=self.config.session_id,
                metadata={
                    "provider": "litellm",
                    "model": self.config.llm.model_name,
                    "base_url": self.config.llm.base_url,
                    "session_id": self.config.session_id,
                },
                input=normalized_messages,
                tags=["llm", "litellm", "completion"],
            )

            # Create generation observation
            generation = trace.generation(
                name="litellm_completion",
                model=self.config.llm.model_name,
                model_parameters={
                    "temperature": self.config.llm.temperature,
                    "max_tokens": completion_params.get("max_tokens"),
                    "top_p": completion_params.get("top_p"),
                },
                input=normalized_messages,
                metadata={
                    "provider": "litellm",
                    "model_name": self.config.llm.model_name,
                    "base_url": self.config.llm.base_url,
                    "completion_params": completion_params,
                },
            )
            return trace, generation
        except Exception as e:  # pragma: no cover - tracing must not break main flow
            logger.warning("Failed to create Langfuse trace: %s", e)
            return None, None

    def create_yandex_trace(
        self,
        y_messages: List[Dict[str, Any]],
        normalized_messages: List[Dict[str, Any]],
        yandex_model_id: str,
        yandex_model_version: str,
    ) -> Tuple[Any, Any]:
        """Create Langfuse trace and generation for Yandex SDK calls."""
        if not self.is_enabled():
            return None, None

        try:
            trace = self._langfuse.trace(
                name="yandex_sdk_llm_call",
                user_id=self.config.session_id,
                metadata={
                    "provider": "yandex_sdk",
                    "model": yandex_model_id,
                    "model_version": yandex_model_version,
                    "folder_id": self.config.llm.yandex_folder_id,
                    "session_id": self.config.session_id,
                },
                input=y_messages,
                tags=["llm", "yandex_sdk", "completion"],
            )
            # Start child generation observation
            generation = trace.generation(
                name="yandex_completion",
                model=yandex_model_id,
                model_parameters={
                    "temperature": self.config.llm.temperature,
                    "version": yandex_model_version,
                    "folder_id": self.config.llm.yandex_folder_id,
                },
                input=y_messages,
                metadata={
                    "provider": "yandex_sdk",
                    "model_id": yandex_model_id,
                    "model_version": yandex_model_version,
                    "folder_id": self.config.llm.yandex_folder_id,
                    "original_messages": normalized_messages,
                },
            )
            return trace, generation
        except Exception as e:  # pragma: no cover - tracing must not break main flow
            logger.warning("Failed to create Langfuse trace for Yandex SDK: %s", e)
            return None, None

    def extract_litellm_usage(self, response) -> Dict[str, int]:
        """Extract usage information from LiteLLM response."""
        usage_info = {}
        if hasattr(response, "usage") and response.usage:
            usage_info = {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }
        return usage_info

    def extract_yandex_usage(self, result) -> Dict[str, int]:
        """Extract usage information from Yandex SDK result."""
        usage_info = {}
        if hasattr(result, "usage") and result.usage:
            usage_info = {
                "input_tokens": getattr(result.usage, "input_text_tokens", 0),
                "output_tokens": getattr(result.usage, "completion_tokens", 0),
                "total_tokens": getattr(result.usage, "total_tokens", 0),
            }
        return usage_info

    def handle_trace_success(
        self,
        trace,
        generation,
        content: str | None,
        usage_info: Dict[str, int],
        response_metadata: Dict[str, Any],
        provider: str,
    ):
        """Handle successful trace completion for both providers."""
        if generation is not None:
            try:
                generation.end(
                    output=content, usage_details=usage_info, metadata=response_metadata
                )
            except Exception as e:  # pragma: no cover
                logger.warning(
                    f"Failed to update Langfuse generation for {provider}: %s", e
                )

        if trace is not None:
            try:
                trace.update(output=content)
            except Exception as e:  # pragma: no cover
                logger.warning(f"Failed to update Langfuse trace for {provider}: %s", e)

    def handle_trace_error(
        self,
        trace,
        generation,
        error: Exception,
        provider: str,
        additional_metadata: Dict[str, Any] | None = None,
    ):
        """Handle error trace completion for both providers."""
        error_metadata = {
            "error_type": type(error).__name__,
            "error_details": str(error),
        }
        if additional_metadata:
            error_metadata.update(additional_metadata)

        if generation is not None:
            try:
                generation.end(
                    output=None,
                    level="ERROR",
                    status_message=str(error),
                    metadata=error_metadata,
                )
            except Exception as update_error:  # pragma: no cover
                logger.warning(
                    f"Failed to update Langfuse generation with error for {provider}: %s",
                    update_error,
                )

        if trace is not None:
            try:
                trace.update(
                    output=None,
                    level="ERROR",
                    status_message=str(error),
                    metadata=error_metadata,
                )
            except Exception as update_error:  # pragma: no cover
                logger.warning(
                    f"Failed to update Langfuse trace with error for {provider}: %s",
                    update_error,
                )

    def flush_traces(self) -> None:
        """Flush all pending Langfuse traces to the server."""
        if self.is_enabled():
            try:
                self._langfuse.flush()
                logger.debug("Successfully flushed Langfuse traces")
            except Exception as e:
                logger.warning("Failed to flush Langfuse traces: %s", e)

    def shutdown(self) -> None:
        """Gracefully shutdown the Langfuse client."""
        if self.is_enabled():
            try:
                self._langfuse.shutdown()
                logger.debug("Successfully shutdown Langfuse client")
            except Exception as e:
                logger.warning("Failed to shutdown Langfuse client: %s", e)
