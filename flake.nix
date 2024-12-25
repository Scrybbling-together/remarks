{
  description = "Remarks - ReMarkable notebook files to human readable formats";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication mkPoetryEnv defaultPoetryOverrides;
        pythonEnv = pkgs.python310.withPackages (ps: with ps; [ ]);

        remarksBin = mkPoetryApplication {
          projectDir = ./.;
          python = pkgs.python310;
          preferWheels = true;
          overrides = defaultPoetryOverrides.extend
          (final: prev: {
            click = prev.click.overridePythonAttrs (
              old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ prev.flit-scm ];
              }
            );
          });
          # Optional overrides if needed:
          # overrides = poetry2nix.overrides.withDefaults (final: prev: { });
        };

        environment = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.poetry
            pkgs.zlib
            pkgs.gnumake
            pkgs.libgcc.lib
            pkgs.poppler_utils
            pkgs.inotify-tools
            pkgs.inkscape
          ];

          shellHook = ''
            echo "🔍 Remarks Development Environment"
            echo "• Run 'poetry install' to set up dependencies"

            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.libgcc.lib pkgs.zlib ]}:$LD_LIBRARY_PATH"

            if ! [[ -f .githooks/pre-commit ]]; then
              git config core.hooksPath .githooks
            fi

            if ! [[ -d .venv ]]; then
              ${pythonEnv}/bin/python -m venv .venv
              source .venv/bin/activate
            else
              source .venv/bin/activate
            fi

            pip install poetry
            poetry install
          '';
        };
      in {
        packages = {
          default = remarksBin;
          remarks = remarksBin;
        };

        devShells.default = environment;
      });
}