import asyncio
import logging
import os
from typing import Any, Dict, List, TypeVar

import httpx
import litellm
from litellm.caching.caching import Cache, LiteLLMCacheType
from pydantic import BaseModel
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from aipg.configs.app_config import AppConfig
from aipg.configs.loader import load_config

try:
    # Optional dependency: used only when provider == "yandex_sdk"
    from yandex_cloud_ml_sdk import YCloudML  # type: ignore
except Exception:  # pragma: no cover - optional import
    YCloudML = None  # type: ignore
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

        if (
            config.langfuse.public_key
            and config.langfuse.secret_key
            and config.langfuse.host
        ):
            os.environ.setdefault("LANGFUSE_PUBLIC_KEY", config.langfuse.public_key)
            os.environ.setdefault("LANGFUSE_SECRET_KEY", config.langfuse.secret_key)
            os.environ.setdefault("LANGFUSE_HOST", config.langfuse.host)
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]

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
        # Normalize to chat message list
        normalized_messages: List[Dict[str, Any]] = (
            [{"role": "user", "content": messages}]
            if isinstance(messages, str)
            else messages
        )
        logger.debug("Sending messages to LLM: %s", normalized_messages)
        content: str | None = None

        # Yandex SDK path: delegate to deferred API for consistency
        if self._provider == "yandex_sdk":
            return await self.query_deferred(normalized_messages)

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
        logger.debug("Received response from LLM: %s", content)
        return content

    async def query_deferred(self, messages: str | List[Dict[str, Any]]) -> str | None:
        """Send an asynchronous request and wait for completion.

        For Yandex SDK, this uses run_deferred().wait(). For other providers, falls back to query().
        """
        if self._provider != "yandex_sdk":
            return await self.query(messages)

        normalized_messages: List[Dict[str, Any]] = (
            [{"role": "user", "content": messages}]
            if isinstance(messages, str)
            else messages
        )
        y_messages = [
            {
                "role": m.get("role", "user"),
                "text": m.get("content") if "content" in m else m.get("text", ""),
            }
            for m in normalized_messages
        ]

        loop = asyncio.get_running_loop()
        operation = await loop.run_in_executor(
            None, lambda: self._yandex_model.run_deferred(y_messages)
        )
        # Wait for completion on a thread
        result = await loop.run_in_executor(None, operation.wait)  # type: ignore
        try:
            content = "".join(str(alt) for alt in result)  # type: ignore
        except Exception:
            content = str(result)
        return content


if __name__ == "__main__":
    config = load_config(schema=AppConfig)
    llm = LLMClient(config)
    print(asyncio.run(llm.query("Hello, how are you?")))
