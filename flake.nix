{
  description = "Remarks - ReMarkable notebook files to human readable formats";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = { url = "github:nix-community/poetry2nix"; };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
          mkPoetryApplication defaultPoetryOverrides;
        pythonEnv = pkgs.python310.withPackages (ps: [ ]);

        remarksBin = mkPoetryApplication {
          projectDir = ./.;
          python = pkgs.python310;
          preferWheels = true;
          overrides = defaultPoetryOverrides.extend (final: prev: {
            click = prev.click.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ prev.flit-scm ];
            });
            rmc = prev.rmc.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry-core ];
            });
          });
          extras = [ "server" ];

          propagatedBuildInputs = [ pkgs.inkscape ];
          nativeCheckInputs = [ pkgs.inkscape ];
          checkPhase = ''
            pytest
          '';
          doCheck = true;
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

            export LD_LIBRARY_PATH="${
              pkgs.lib.makeLibraryPath [ pkgs.libgcc.lib pkgs.zlib ]
            }:$LD_LIBRARY_PATH"

            if ! [[ -f .githooks/pre-commit ]]; then
              git config core.hooksPath .githooks
            fi

            if ! [[ -d .venv ]]; then
              ${pythonEnv}/bin/python -m venv .venv
              source .venv/bin/activate
            else
              source .venv/bin/activate
            fi

            poetry install
          '';
        };

        dockerBinary = pkgs.dockerTools.buildImage {
          name = "remarks-bin";
          config = { Entrypoint = [ "${remarksBin}/bin/remarks" ]; };
        };
        dockerServer = pkgs.dockerTools.buildLayeredImage {
          name = "remarks-server";
          config = { Entrypoint = [ "${remarksBin}/bin/remarks-server" ]; };
        };
      in {
        packages = {
          default = remarksBin;
          remarks = remarksBin;
          dockerServer = dockerServer;
          dockerBin = dockerBinary;
        };

        checks.default = remarksBin;

        apps.default = {
          type = "app";
          program = "${remarksBin}/bin/remarks";
        };

        devShells.default = environment;
      });
}
