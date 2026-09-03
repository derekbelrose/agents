#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

required_files=(
  .gitignore
  AGENTS.md
  PLAN.md
  README.md
  docs/architecture.md
  flake.lock
  flake.nix
  tests/milestone1.sh
)

required_directories=(
  agents/research/prompts
  agents/research/schemas
  agents/research/src
  docs
  tests
  tools/web-search/src
)

for path in "${required_files[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "missing required file: $path" >&2
    exit 1
  fi
done

for path in "${required_directories[@]}"; do
  if [[ ! -d "$path" ]]; then
    echo "missing required directory: $path" >&2
    exit 1
  fi
done

if ! grep -Fq 'nix develop' README.md; then
  echo 'README.md must document nix develop' >&2
  exit 1
fi

if ! grep -Fq 'nix flake check' README.md; then
  echo 'README.md must document nix flake check' >&2
  exit 1
fi

if ! grep -Fq 'Nix dependency relationship' docs/architecture.md; then
  echo 'architecture must distinguish composition from isolation' >&2
  exit 1
fi

if grep -Eq '(^|/)(orchestrator|memory-agent|mcp|rag)(/|$)' <(
  find . -mindepth 1 -type d -not -path './.git*' -print
); then
  echo 'repository contains a bootstrap non-goal component' >&2
  exit 1
fi

echo 'Milestone 1 repository checks passed.'
