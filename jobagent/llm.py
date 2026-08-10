"""Thin, resilient wrapper around a local Ollama server.

Everything the agent 'thinks' with goes through here. No cloud calls, ever.
"""
from __future__ import annotations

import json
import logging
import math
import re
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import load_config

log = logging.getLogger("jobagent.llm")


class OllamaError(RuntimeError):
    pass


class LLM:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_config()
        self.host = self.cfg.llm.host.rstrip("/")
        # Ollama is on localhost. Never route it through a system/corporate proxy
        # — trust_env=False also stops httpx choking on an unsupported proxy scheme.
        local = any(h in self.host for h in ("localhost", "127.0.0.1", "0.0.0.0", "::1"))
        self._client = httpx.Client(
            timeout=self.cfg.llm.request_timeout_s,
            trust_env=not local,
        )

    # -- health --------------------------------------------------------------
    def is_up(self) -> bool:
        try:
            r = self._client.get(f"{self.host}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def installed_models(self) -> List[str]:
        try:
            r = self._client.get(f"{self.host}/api/tags", timeout=10)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def ensure_models(self) -> Dict[str, bool]:
        have = {m.split(":")[0]: True for m in self.installed_models()}
        full = set(self.installed_models())
        out = {}
        for m in (self.cfg.llm.chat_model, self.cfg.llm.embed_model):
            out[m] = (m in full) or (m.split(":")[0] in have)
        return out

    # -- generation ----------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20), reraise=True)
    def chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        temperature: Optional[float] = None,
        num_ctx: Optional[int] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "model": self.cfg.llm.chat_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.cfg.llm.temperature if temperature is None else temperature,
                "num_ctx": num_ctx or self.cfg.llm.num_ctx,
            },
        }
        if json_mode:
            payload["format"] = "json"
        r = self._client.post(f"{self.host}/api/chat", json=payload)
        if r.status_code != 200:
            raise OllamaError(f"ollama {r.status_code}: {r.text[:300]}")
        return (r.json().get("message") or {}).get("content", "").strip()

    def chat_json(self, system: str, user: str, fallback: Optional[Dict] = None, **kw) -> Dict[str, Any]:
        """Ask for JSON, and actually get JSON back even when the model rambles."""
        try:
            raw = self.chat(system, user, json_mode=True, **kw)
        except Exception as e:  # noqa: BLE001
            log.warning("chat_json failed: %s", e)
            return fallback or {}
        return _coerce_json(raw, fallback or {})

    # -- embeddings ----------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def embed(self, text: str) -> List[float]:
        text = (text or "")[:8000]
        r = self._client.post(
            f"{self.host}/api/embeddings",
            json={"model": self.cfg.llm.embed_model, "prompt": text},
        )
        if r.status_code != 200:
            raise OllamaError(f"embed {r.status_code}: {r.text[:200]}")
        return r.json().get("embedding", [])

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


# ---------------------------------------------------------------------------

def _coerce_json(raw: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    if not raw:
        return fallback
    raw = raw.strip()
    # strip ```json fences
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except Exception:
        pass
    # grab the largest {...} block
    start, depth = raw.find("{"), 0
    if start >= 0:
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start : i + 1])
                    except Exception:
                        break
    return fallback


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


_llm: Optional[LLM] = None


def get_llm() -> LLM:
    global _llm
    if _llm is None:
        _llm = LLM()
    return _llm
