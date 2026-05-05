from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

import httpx
from sqlmodel import Session, select

from app.models.entities import LlmProviderSetting

LlmTask = Literal["chunking", "question_generation"]


class LlmGatewayError(ValueError):
    """表示大模型调用网关中的可预期错误。"""


@dataclass
class LlmProviderConfig:
    """描述一次可实际发起调用的大模型厂商配置。"""

    provider_id: int
    provider_name: str
    display_name: str
    base_url: str
    api_key: str
    model: str


@dataclass
class LlmConnectivityResult:
    """描述一次厂商连通性测试的返回结果。"""

    success: bool
    provider_name: str
    display_name: str
    model: str
    base_url: str
    message: str


class LlmGatewayService:
    """统一负责读取已启用厂商配置并发起 OpenAI 兼容调用。"""

    task_flag_mapping = {
        "chunking": "use_for_chunking",
        "question_generation": "use_for_question_generation",
    }
    default_base_urls = {
        "openrouter": "https://openrouter.ai/api/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "siliconflow": "https://api.siliconflow.cn/v1",
        "openai": "https://api.openai.com/v1",
    }

    def get_active_provider_for_task(self, session: Session, task: LlmTask) -> LlmProviderConfig | None:
        """返回某个任务当前启用的大模型厂商配置，没有则返回 None。"""
        flag_name = self.task_flag_mapping[task]
        statement = (
            select(LlmProviderSetting)
            .where(
                LlmProviderSetting.is_enabled == True,
                getattr(LlmProviderSetting, flag_name) == True,
            )
            .order_by(LlmProviderSetting.updated_at.desc(), LlmProviderSetting.id.desc())
        )
        provider = session.exec(statement).first()
        if provider is None:
            return None
        return self._build_provider_config(provider)

    def build_provider_config(
        self,
        *,
        provider_name: str,
        display_name: str,
        base_url: str | None,
        api_key: str,
        default_model: str | None,
        provider_id: int = 0,
    ) -> LlmProviderConfig:
        """基于前端传入的厂商配置构建标准化的调用配置。"""
        provider = LlmProviderSetting(
            id=provider_id or None,
            provider_name=provider_name,
            display_name=display_name,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
        )
        config = self._build_provider_config(provider)
        if config is None:
            raise LlmGatewayError("厂商配置不完整，至少需要可用的 api_key 和 model。")
        return config

    def test_provider_connectivity(
        self,
        *,
        provider_name: str,
        display_name: str,
        base_url: str | None,
        api_key: str,
        default_model: str | None,
        timeout: float = 15.0,
    ) -> LlmConnectivityResult:
        """使用给定配置发起最小请求，验证厂商连通性。"""
        provider = self.build_provider_config(
            provider_name=provider_name,
            display_name=display_name,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
        )

        try:
            content = self._request_chat_completion_content(
                provider,
                system_prompt="你是一个只会回复 pong 的连通性测试助手。",
                user_prompt="ping",
                temperature=0.0,
                timeout=timeout,
                max_tokens=8,
            )
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise LlmGatewayError(f"连通性测试失败，HTTP 状态码：{status_code}。") from exc
        except httpx.HTTPError as exc:
            raise LlmGatewayError(f"连通性测试失败：{exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise LlmGatewayError("连通性测试失败：厂商返回格式不符合预期。") from exc

        message = content.strip() or "调用成功，但返回内容为空。"
        return LlmConnectivityResult(
            success=True,
            provider_name=provider.provider_name,
            display_name=provider.display_name,
            model=provider.model,
            base_url=provider.base_url,
            message=message,
        )

    def chat_json(
        self,
        session: Session,
        task: LlmTask,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        timeout: float = 20.0,
    ) -> dict | None:
        """按任务读取当前启用厂商并请求 JSON 结果，请求失败时返回 None。"""
        provider = self.get_active_provider_for_task(session, task)
        if provider is None:
            return None

        try:
            content = self._request_chat_completion_content(
                provider,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                timeout=timeout,
            )
            return self._parse_json_content(content)
        except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError):
            return None

    def _build_provider_config(self, provider: LlmProviderSetting) -> LlmProviderConfig | None:
        """把数据库实体或临时配置转换成标准化调用配置。"""
        base_url = (
            provider.base_url
            or self.default_base_urls.get(provider.provider_name.lower())
            or self.default_base_urls["openai"]
        ).rstrip("/")
        model = (provider.default_model or "").strip()
        api_key = (provider.api_key or "").strip()
        if not model or not api_key:
            return None

        return LlmProviderConfig(
            provider_id=provider.id or 0,
            provider_name=provider.provider_name,
            display_name=provider.display_name,
            base_url=base_url,
            api_key=api_key,
            model=model,
        )

    def _request_chat_completion_content(
        self,
        provider: LlmProviderConfig,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout: float,
        max_tokens: int | None = None,
    ) -> str:
        """调用 OpenAI 兼容聊天接口并返回 message content。"""
        url = self._build_chat_completions_url(provider.base_url)
        payload = {
            "model": provider.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    def _build_chat_completions_url(self, base_url: str) -> str:
        """把厂商配置中的 base_url 规范化为 chat completions 地址。"""
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return normalized
        return f"{normalized}/chat/completions"

    def _parse_json_content(self, content: str) -> dict:
        """解析模型返回的 JSON 文本，兼容 ```json 包裹格式。"""
        cleaned = content.strip()
        fenced_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if fenced_match is not None:
            cleaned = fenced_match.group(1).strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not a JSON object.")
        return parsed


llm_gateway_service = LlmGatewayService()