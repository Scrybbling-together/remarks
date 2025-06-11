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
          mkPoetryEnv mkPoetryApplication defaultPoetryOverrides;

          poetryArgs = {
            python = pkgs.python312;
            projectDir = ./.;
            preferWheels = true;
            overrides = defaultPoetryOverrides.extend (final: prev: {
              click = prev.click.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ prev.flit-scm ];
              });
              rmc = prev.rmc.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry-core ];
              });
            });
          };

          pythonEnv = mkPoetryEnv (poetryArgs);

        remarksBin = mkPoetryApplication (poetryArgs // {
          extras = [ "server" ];

          propagatedBuildInputs = [ pkgs.inkscape ];
          nativeCheckInputs = [ pkgs.inkscape ];
        });

        environment = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.poppler_utils
            pkgs.inotify-tools
            pkgs.inkscape
            pkgs.gum
          ];

          shellHook = ''
            if ! [[ -f .githooks/pre-commit ]]; then
              git config core.hooksPath .githooks
            fi

            echo "🔍 Remarks Development Environment"
            echo "Nix configured git hooks and activated the python environment for you :)"

            echo "To run remarks:"
            echo "python -m remarks {IN_FILE.rmn} {OUTPUT_LOCATION}"

            echo ""
            echo "To test remarks:"
            echo "pytest -m \"not unfinished_feature\""
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