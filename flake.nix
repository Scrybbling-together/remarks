{
  description = "Remarks - ReMarkabe notebook files to human readable formats";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python310.withPackages (ps: with ps; []);
      in
      {
        devShells.default = pkgs.mkShell {
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

            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
              pkgs.libgcc.lib
              pkgs.zlib
            ]}:$LD_LIBRARY_PATH"

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
      }
    );
}