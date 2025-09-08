import logging
import os
from typing import Any, Dict, List, TypeVar

import litellm
from litellm.caching.caching import Cache, LiteLLMCacheType
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from aipg.configs.app_config import AppConfig

T = TypeVar("T", bound=BaseModel)

# litellm._logging._disable_debugging()
# litellm._turn_on_debug()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config: AppConfig):
        self.config = config

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

        self.completion_params = {
            "model": f"{config.llm.model_name}",
            "api_key": self.config.llm.api_key,
            "base_url": self.config.llm.base_url,
            "extra_headers": self.config.llm.extra_headers,
            "metadata": {"session_id": config.session_id},
            **self.config.llm.completion_params,
        }

        if config.llm.caching.enabled:
            litellm.cache = Cache(
                type=LiteLLMCacheType.DISK, disk_cache_dir=config.llm.caching.dir_path
            )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception(
            lambda e: getattr(e, "status_code", None) in {408, 409, 429, 500, 502, 503, 504}
            or isinstance(e, (TimeoutError, ConnectionError))
        ),
        reraise=True,
    )
    def query(self, messages: str | List[Dict[str, Any]]) -> str | None:
        messages = (
            [{"role": "user", "content": messages}]
            if isinstance(messages, str)
            else messages
        )
        logger.debug("Sending messages to LLM: %s", messages)
        response = litellm.completion(
            messages=messages,
            **self.completion_params,
        )
        logger.debug(
            "Received response from LLM: %s", response.choices[0].message.content
        )
        return response.choices[0].message.content
