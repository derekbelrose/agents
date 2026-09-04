import pytest
from conftest import ROOT


@pytest.mark.milestone7
def test_agents_md_documents_codex_invocation() -> None:
    guidance = (ROOT / "AGENTS.md").read_text()
    assert 'research-agent "' in guidance
    assert "research-agent --json" in guidance
    assert "source provenance" in guidance.lower()


@pytest.mark.milestone7
def test_codex_guidance_does_not_require_special_integration() -> None:
    guidance = (ROOT / "AGENTS.md").read_text().lower()
    assert "codex-specific api" not in guidance
