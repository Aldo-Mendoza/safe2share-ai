import os
import pytest

from safe2share.providers import Provider
from safe2share.service import Safe2ShareService


def test_local_provider_initializes():
    svc = Safe2ShareService(provider=Provider.LOCAL)
    assert svc.provider == Provider.LOCAL


def test_llm_provider_requires_config(monkeypatch):
    monkeypatch.delenv("S2S_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("S2S_LLM_MODEL", raising=False)

    with pytest.raises(RuntimeError):
        Safe2ShareService(provider=Provider.LLM)
