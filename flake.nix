{
  description = "Nix-packaged agent toolkit";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      checks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          repository-layout = pkgs.runCommand "ai-agents-repository-layout" { src = ./.; } ''
            test -s "$src/README.md"
            test -s "$src/AGENTS.md"
            test -s "$src/PLAN.md"
            test -s "$src/docs/architecture.md"
            test -s "$src/agents/research/README.md"
            test -s "$src/tools/README.md"
            test -s "$src/tests/README.md"
            touch "$out"
          '';

          contract-tests-collect =
            pkgs.runCommand "research-agent-contract-tests-collect"
              {
                src = ./.;
                nativeBuildInputs = [
                  pkgs.python3Packages.jsonschema
                  pkgs.python3Packages.pytest
                ];
              }
              ''
                pytest --collect-only -q "$src/tests"
                touch "$out"
              '';
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
              ruff
              uv
              python3Packages.jsonschema
              python3Packages.pytest
            ];

            UV_PYTHON = "${pkgs.python3}/bin/python3";
            UV_PYTHON_DOWNLOADS = "never";
          };
        }
      );

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt);
    };
}
