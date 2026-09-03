from pathlib import Path

import pytest
from conftest import ROOT


@pytest.mark.milestone1
def test_repository_foundation_is_present() -> None:
    expected = {
        "AGENTS.md",
        "PLAN.md",
        "README.md",
        "agents/research/prompts",
        "agents/research/schemas",
        "agents/research/src",
        "docs/architecture.md",
        "flake.lock",
        "flake.nix",
        "tools/web-search/src",
    }
    missing = sorted(path for path in expected if not (ROOT / path).exists())
    assert not missing, f"missing Milestone 1 paths: {missing}"


@pytest.mark.milestone1
def test_architecture_records_required_boundaries() -> None:
    architecture = " ".join((ROOT / "docs/architecture.md").read_text().split())
    for statement in (
        "independently executable",
        "Machine-mode stdout",
        "does not, by itself, provide runtime security isolation",
        "No component exposes arbitrary shell execution",
    ):
        assert statement in architecture


@pytest.mark.milestone1
def test_readme_documents_development_commands() -> None:
    readme = (ROOT / "README.md").read_text()
    assert "nix develop" in readme
    assert "nix flake check" in readme


@pytest.mark.milestone1
def test_no_bootstrap_nongoal_component_directories_exist() -> None:
    forbidden = {"orchestrator", "memory-agent", "mcp", "rag"}
    directories = {path.name for path in ROOT.rglob("*") if path.is_dir()}
    assert forbidden.isdisjoint(directories)


def test_test_file_is_inside_repository() -> None:
    assert Path(__file__).is_relative_to(ROOT)
