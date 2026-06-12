"""LLM API client for OpenAI-compatible providers."""

from __future__ import annotations

import time
from typing import List, Optional

from openai import OpenAI


class LLMClient:
    """OpenAI-compatible LLM client."""

    def __init__(self, config: dict):
        llm_cfg = config["llm"]
        self.client = OpenAI(
            api_key=llm_cfg["api_key"],
            base_url=llm_cfg["base_url"],
            timeout=llm_cfg.get("timeout", 20),
            max_retries=0,
        )
        self.model = llm_cfg["model"]
        self.temperature = llm_cfg.get("temperature", 0.7)
        self.max_tokens = llm_cfg.get("max_tokens", 2048)
        self._max_retries = max(1, int(llm_cfg.get("retries", 1)))

    def chat(
        self,
        messages: List[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature if temperature is None else temperature,
                    max_tokens=self.max_tokens if max_tokens is None else max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:  # pragma: no cover - network failures vary
                last_error = exc
                if attempt < self._max_retries - 1:
                    time.sleep(2**attempt)

        raise RuntimeError(f"LLM API 调用失败（重试 {self._max_retries} 次后）: {last_error}")

    def answer(self, prompt: str, **kwargs) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    def chat_stream(
        self,
        messages: List[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """流式调用 LLM，逐 chunk 返回 delta 文本。

        注意：流式模式下不做应用层重试，因为 stream 不可回放。
        网络中断由 OpenAI SDK 自身的 connect timeout 覆盖。
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices else ""
            if delta:
                yield delta

    def answer_stream(self, prompt: str, **kwargs):
        """流式单轮问答。"""
        messages = [{"role": "user", "content": prompt}]
        yield from self.chat_stream(messages, **kwargs)

    def summarize_long_text(self, text: str) -> str:
        estimated_tokens = len(text) / 1.5
        if estimated_tokens <= self.max_tokens * 0.7:
            return self.answer(text)

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < self.max_tokens * 1.0:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n\n"
        if current:
            chunks.append(current.strip())

        summaries = []
        for chunk in chunks:
            prompt = "请对以下文本进行简要摘要，保留核心信息：\n\n" + chunk
            summaries.append(self.answer(prompt, max_tokens=512))

        merged = "\n\n---\n\n".join(summaries)
        final_prompt = "请将以下多段摘要整合为一段连贯的结构化摘要：\n\n" + merged
        return self.answer(final_prompt)
