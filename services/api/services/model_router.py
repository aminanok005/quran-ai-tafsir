"""Central task-to-model routing with bounded fallback and usage tracking."""

from __future__ import annotations

import time
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Optional

from ..config import Settings, settings as default_settings
from .gemini_provider import GeminiError, GeminiProvider, GeminiResult, GeminiErrorKind


class Task(str, Enum):
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    RAG_ANSWER = "rag_answer"
    CONTENT = "content"
    TAFSIR_ANALYSIS = "tafsir_analysis"
    IKHTILAF = "ikhtilaf"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"
    CLASSIFICATION = "classification"
    METADATA = "metadata"


_TIER = {
    Task.TRANSLATION: "primary", Task.SUMMARIZATION: "primary", Task.RAG_ANSWER: "primary", Task.CONTENT: "primary",
    Task.TAFSIR_ANALYSIS: "reasoning", Task.IKHTILAF: "reasoning", Task.EVIDENCE_SYNTHESIS: "reasoning",
    Task.CLASSIFICATION: "fast", Task.METADATA: "fast",
}


class ModelRouter:
    def __init__(self, provider: Optional[GeminiProvider] = None, config: Settings = default_settings, clock: Callable[[], float] = time.monotonic):
        self.config = config
        self._clock = clock
        self._cooldowns: dict[str, float] = {}
        self.provider = provider or GeminiProvider(config)
        self.usage: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0})

    def models_for(self, task: Task) -> list[str]:
        c = self.config
        tier = {"primary": c.primary_model, "reasoning": c.reasoning_model or c.primary_model, "fast": c.fast_model or c.primary_model}[_TIER[task]]
        chain: list[str] = []
        for model in (tier, c.fallback_model):
            if model and model not in chain:
                chain.append(model)
        return chain

    async def run(self, task: Task, messages: list[dict[str, str]], *, json_output: bool = False, **kwargs: Any) -> GeminiResult:
        chain = self.models_for(task)
        if not chain:
            raise GeminiError(GeminiErrorKind.CONFIGURATION)
        last: Optional[GeminiError] = None
        now = self._clock()
        ready = [m for m in chain if self._cooldowns.get(m, 0.0) <= now]
        for model in ready or chain:  # each model is tried once; the provider bounds its own retries
            try:
                result = await self.provider.generate(model, messages, json_output=json_output, **kwargs)
            except GeminiError as error:
                last = error
                if error.kind in {GeminiErrorKind.RATE_LIMIT, GeminiErrorKind.SERVER, GeminiErrorKind.TIMEOUT}:
                    self._cooldowns[model] = self._clock() + self.config.tts_model_cooldown_seconds
                if error.kind in {GeminiErrorKind.CONFIGURATION, GeminiErrorKind.AUTHENTICATION}:
                    break
                continue
            self._track(result)
            return result
        assert last is not None
        raise last

    def _track(self, result: GeminiResult) -> None:
        entry = self.usage[result.usage.model]
        entry["calls"] += 1
        entry["prompt_tokens"] += result.usage.prompt_tokens
        entry["completion_tokens"] += result.usage.completion_tokens
        entry["cost"] += result.usage.cost or 0.0
