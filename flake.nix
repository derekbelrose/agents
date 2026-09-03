{
  description = "Nix-packaged agent toolkit";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          research-agent = pkgs.callPackage ./agents/research/default.nix { };
          web-search-tool = pkgs.callPackage ./tools/web-search/default.nix { };
          default = self.packages.${system}.research-agent;
        }
      );

      apps = forAllSystems (system: {
        research-agent = {
          type = "app";
          program = "${self.packages.${system}.research-agent}/bin/research-agent";
          meta.description = "Protocol-first research agent";
        };
        web-search-tool = {
          type = "app";
          program = "${self.packages.${system}.web-search-tool}/bin/web-search";
          meta.description = "Deterministic Brave web search tool";
        };
        default = self.apps.${system}.research-agent;
      });

      checks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          research-agent = self.packages.${system}.research-agent;
          web-search-tool = self.packages.${system}.web-search-tool;
        in
        {
          repository-layout = pkgs.runCommand "ai-agents-repository-layout" { src = ./.; } ''
            test -s "$src/README.md"
            test -s "$src/AGENTS.md"
            test -s "$src/PLAN.md"
            test -s "$src/docs/architecture.md"
            test -s "$src/docs/protocol.md"
            test -s "$src/agents/research/README.md"
            test -s "$src/tools/README.md"
            test -s "$src/tools/web-search/README.md"
            test -s "$src/tests/README.md"
            test -s "$src/secretspec.toml"
            touch "$out"
          '';

          contract-tests =
            pkgs.runCommand "research-agent-contract-tests"
              {
                src = ./.;
                nativeBuildInputs = [
                  pkgs.python3Packages.jsonschema
                  pkgs.python3Packages.pytest
                  research-agent
                ];
              }
              ''
                RESEARCH_AGENT_BIN="${research-agent}/bin/research-agent" \
                  pytest -p no:cacheprovider -q \
                    "$src/tests/test_research_agent_contract.py"
                touch "$out"
              '';

          model-client-tests =
            pkgs.runCommand "model-client-tests"
              {
                src = ./.;
                nativeBuildInputs = [
                  pkgs.python3Packages.pytest
                  research-agent
                ];
              }
              ''
                PYTHONPATH="${research-agent}/${pkgs.python3.sitePackages}" \
                  pytest -p no:cacheprovider -q \
                  "$src/tests/test_model_client.py"
                touch "$out"
              '';

          web-search-tests =
            pkgs.runCommand "web-search-tests"
              {
                src = ./.;
                nativeBuildInputs = [
                  pkgs.python3Packages.jsonschema
                  pkgs.python3Packages.pytest
                  web-search-tool
                ];
              }
              ''
                WEB_SEARCH_BIN="${web-search-tool}/bin/web-search" \
                  pytest -p no:cacheprovider -q \
                  "$src/tests/test_web_search.py"
                touch "$out"
              '';

          inherit research-agent web-search-tool;
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              git
              jq
              nixfmt
              python3
              secretspec
              uv
            ];

            UV_PYTHON = "${pkgs.python3}/bin/python3";
            UV_PYTHON_DOWNLOADS = "never";
          };
        }
      );

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt);
    };
}
