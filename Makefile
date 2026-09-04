.PHONY: test test-current test-milestone-% check

test:
	uv run --frozen pytest

test-current:
	uv run --frozen pytest -m milestone1

test-milestone-%:
	uv run --frozen pytest -m milestone$*

check:
	uv run --frozen ruff check .
	nix fmt -- --check flake.nix
	nix flake check
