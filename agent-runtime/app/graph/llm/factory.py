import os

from app.graph.llm.port import LlmPort
from app.graph.llm.provider import ProviderLlm
from app.graph.llm.seed_stub import SeedStubLlm


def llm_from_env() -> LlmPort:
    """Prefer the seed stub when FABRIC_LLM_STUB is truthy; otherwise ProviderLlm."""
    flag = os.environ.get("FABRIC_LLM_STUB", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return SeedStubLlm()
    return ProviderLlm()
