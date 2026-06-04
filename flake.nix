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
        });

        environment = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.zotero
            pkgs.inotify-tools
            pkgs.gum
            pkgs.poetry

            # PDF utility tools
            # poppler's `pdfinfo` is great for reading pdf metadata
            pkgs.poppler_utils
            # qpdf is useful to modify pdf metadata
            pkgs.qpdf
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
          config = {
            Entrypoint = [ "${remarksBin}/bin/remarks-server" ];
            # Health check so `docker` / compose can gate on `service_healthy`.
            # The image has no shell or curl, so use the python that is already
            # in the closure to hit the /health route. Honors REMARKS_BIND_PORT.
            # `s` = one second expressed in nanoseconds (Docker image-config format).
            Healthcheck = let s = 1000000000; in {
              Test = [
                "CMD" "${pkgs.python312}/bin/python3" "-c"
                "import os,urllib.request,sys; p=os.getenv('REMARKS_BIND_PORT','5000'); sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:%s/health' % p).getcode()==200 else 1)"
              ];
              Interval = 30 * s;
              Timeout = 5 * s;
              StartPeriod = 20 * s;
              Retries = 3;
            };
          };
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