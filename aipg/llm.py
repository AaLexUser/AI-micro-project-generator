import asyncio
import logging
from typing import Any, Dict, List, TypeVar

import httpx
import litellm
from litellm.caching.caching import Cache, LiteLLMCacheType
from pydantic import BaseModel
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from aipg.configs.app_config import AppConfig
from aipg.configs.loader import load_config
from aipg.tracing import LangfuseTracer
from yandex_cloud_ml_sdk import YCloudML

try:
    from yandex_cloud_ml_sdk._models.completions.function import AsyncCompletions
except ImportError:
    AsyncCompletions = None  # type: ignore

T = TypeVar("T", bound=BaseModel)

# litellm._logging._disable_debugging()
# litellm._turn_on_debug()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self._provider = (config.llm.provider or "").lower().strip() or None

        # If provider is not explicitly set, allow deriving it from model_name prefix
        # Example: "yandex-sdk/yandexgpt" -> provider=yandex_sdk, model_id=yandexgpt
        parsed_model_name = self.config.llm.model_name
        if not self._provider and "/" in parsed_model_name:
            prefix, remainder = parsed_model_name.split("/", 1)
            prefix_lower = prefix.lower().strip()
            if prefix_lower in {"yandex-sdk", "yandexsdk", "yc-sdk", "yc"}:
                self._provider = "yandex_sdk"
                parsed_model_name = remainder
            else:
                # For prefixes like openai/, gemini/, keep default litellm path
                parsed_model_name = self.config.llm.model_name

        # Initialize tracing
        self._tracer = LangfuseTracer(config)

        if not self.config.llm.api_key:
            raise ValueError(
                "API key not provided and AIPG_LLM_API_KEY environment variable not set"
            )

        # Provider-specific initialization
        if self._provider == "yandex_sdk":
            if YCloudML is None:
                raise RuntimeError(
                    "yandex-cloud-ml-sdk is not available. Ensure dependency is installed."
                )
            if AsyncCompletions is None:
                raise RuntimeError(
                    "AsyncCompletions is not available. Ensure yandex-cloud-ml-sdk version supports async completions."
                )
            if not self.config.llm.yandex_folder_id:
                raise ValueError(
                    "Yandex SDK selected but AIPG_YANDEX_FOLDER_ID is not set"
                )
            self._yandex_sdk = YCloudML(
                folder_id=self.config.llm.yandex_folder_id,
                auth=self.config.llm.api_key,
            )
            self._yandex_model_id = parsed_model_name
            self._yandex_model_version = (
                self.config.llm.yandex_model_version or "latest"
            )
            # Use AsyncCompletions to create the model
            self._yandex_model = self._yandex_sdk.models.completions(
                self._yandex_model_id, model_version=self._yandex_model_version
            )
            # Configure temperature if provided
            if self.config.llm.temperature is not None:
                self._yandex_model = self._yandex_model.configure(
                    temperature=self.config.llm.temperature
                )
        else:
            # Default: use litellm with OpenAI-compatible providers
            self.completion_params = {
                "model": f"{config.llm.model_name}",
                "api_key": self.config.llm.api_key,
                "base_url": self.config.llm.base_url,
                "extra_headers": self.config.llm.extra_headers,
                "metadata": {"session_id": config.session_id},
                **self.config.llm.completion_params,
            }
            print(f"completion_params: {self.completion_params}")
            self.completion_params.setdefault("timeout", 60)

        if config.llm.caching.enabled:
            litellm.cache = Cache(
                type=LiteLLMCacheType.DISK, disk_cache_dir=config.llm.caching.dir_path
            )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(
            retry_if_exception(
                lambda e: getattr(e, "status_code", None)
                in {408, 409, 429, 500, 502, 503, 504}
            )
            | retry_if_exception(
                lambda e: isinstance(
                    e,
                    (
                        TimeoutError,
                        ConnectionError,
                        httpx.TimeoutException,
                        httpx.ConnectError,
                    ),
                )
            )
        ),
        reraise=True,
    )
    async def query(self, messages: str | List[Dict[str, Any]]) -> str | None:
        normalized_messages = self._tracer.normalize_messages(messages)
        logger.debug("Sending messages to LLM: %s", normalized_messages)

        # Yandex SDK path: delegate to deferred API for consistency
        if self._provider == "yandex_sdk":
            return await self.query_deferred(normalized_messages)

        # Manual Langfuse tracing for litellm path
        trace, generation = self._tracer.create_litellm_trace(
            normalized_messages, self.completion_params
        )

        try:
            # Default litellm path
            response = await litellm.acompletion(
                messages=normalized_messages,
                **self.completion_params,
            )
            choices = getattr(response, "choices", []) or []
            response_content_any: Any | None = (
                getattr(choices[0].message, "content", None)
                if choices and getattr(choices[0], "message", None)
                else None
            )
            content = (
                str(response_content_any) if response_content_any is not None else None
            )

            # Update generation with success details
            usage_info = self._tracer.extract_litellm_usage(response)
            response_metadata = {
                "response_choices_count": len(choices),
                "model_used": getattr(response, "model", self.config.llm.model_name),
                "finish_reason": getattr(choices[0], "finish_reason", None)
                if choices
                else None,
            }
            self._tracer.handle_trace_success(
                trace, generation, content, usage_info, response_metadata, "litellm"
            )

        except Exception as e:
            # Update generation with error details
            self._tracer.handle_trace_error(trace, generation, e, "litellm")
            # Re-raise the original exception
            raise

        logger.debug("Received response from LLM: %s", content)
        return content

    async def query_deferred(self, messages: str | List[Dict[str, Any]]) -> str | None:
        """Send an asynchronous request using the async run() method.

        For Yandex SDK, this uses the async run() method. For other providers, falls back to query().
        """
        if self._provider != "yandex_sdk":
            return await self.query(messages)

        normalized_messages = self._tracer.normalize_messages(messages)
        y_messages = [
            {
                "role": m.get("role", "user"),
                "text": m.get("content") if "content" in m else m.get("text", ""),
            }
            for m in normalized_messages
        ]

        # Enhanced Langfuse tracing for Yandex SDK calls
        trace, generation = self._tracer.create_yandex_trace(
            y_messages,
            normalized_messages,
            self._yandex_model_id,
            self._yandex_model_version,
        )

        try:
            # Use the async run() method directly
            # Check if the model's run method is actually async or sync
            if hasattr(
                self._yandex_model.run, "__call__"
            ) and asyncio.iscoroutinefunction(self._yandex_model.run):
                result = await self._yandex_model.run(y_messages, timeout=180)
            else:
                # Fall back to running in executor if it's synchronous
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, lambda: self._yandex_model.run(y_messages, timeout=180)
                )

            # Handle GPTModelResult properly
            content = self._extract_content_from_result(result)

            # Update generation with success details
            usage_info = self._tracer.extract_yandex_usage(result)
            response_metadata = {
                "result_type": type(result).__name__,
                "alternatives_count": len(getattr(result, "alternatives", [])),
                "model_used": self._yandex_model_id,
                "model_version": self._yandex_model_version,
            }
            self._tracer.handle_trace_success(
                trace, generation, content, usage_info, response_metadata, "yandex_sdk"
            )

        except Exception as e:
            # Update generation with error details
            additional_metadata = {
                "model_id": self._yandex_model_id,
                "model_version": self._yandex_model_version,
            }
            self._tracer.handle_trace_error(
                trace, generation, e, "yandex_sdk", additional_metadata
            )
            # Re-raise the original exception
            raise

        return content

    def _extract_content_from_result(self, result) -> str | None:
        """Extract text content from GPTModelResult.

        Args:
            result: GPTModelResult object from Yandex SDK

        Returns:
            Extracted text content from first alternative or None if no content available
        """
        try:
            # Handle GPTModelResult with alternatives - return first alternative only
            if hasattr(result, "alternatives") and result.alternatives:
                first_alternative = result.alternatives[0]
                if hasattr(first_alternative, "text") and first_alternative.text:
                    return first_alternative.text
                return None

            # Fallback: try to access text property directly
            if hasattr(result, "text"):
                return result.text

            # Last resort: convert to string
            return str(result) if result is not None else None

        except Exception:
            # If all else fails, convert to string
            return str(result) if result is not None else None

    def flush_traces(self) -> None:
        """Flush all pending Langfuse traces to the server.

        This method should be called before application shutdown to ensure
        all traces are sent to Langfuse.
        """
        self._tracer.flush_traces()

    def shutdown(self) -> None:
        """Gracefully shutdown the Langfuse client.

        This method should be called before application shutdown to ensure
        all traces are sent and resources are properly cleaned up.
        """
        self._tracer.shutdown()


if __name__ == "__main__":
    config = load_config(schema=AppConfig)
    llm = LLMClient(config)
    try:
        print(asyncio.run(llm.query("Hello, how are you?")))
    finally:
        # Ensure traces are flushed before exit
        llm.flush_traces()
