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
          default = self.packages.${system}.research-agent;
        }
      );

      apps = forAllSystems (system: {
        research-agent = {
          type = "app";
          program = "${self.packages.${system}.research-agent}/bin/research-agent";
          meta.description = "Protocol-first research agent";
        };
        default = self.apps.${system}.research-agent;
      });

      checks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          research-agent = self.packages.${system}.research-agent;
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
            test -s "$src/tests/README.md"
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
                  pytest -p no:cacheprovider -q "$src/tests"
                touch "$out"
              '';

          inherit research-agent;
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
