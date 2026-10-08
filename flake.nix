{
  description = "Remarks - ReMarkable notebook files to human readable formats";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (nixpkgs) lib;

        # Single source of truth for the interpreter
        python = pkgs.python312;

        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

        overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

        # The git
        # dependencies are poetry projects published without wheels, so they get
        # built from source and need their build backend declared explicitly.
        pyprojectOverrides = final: prev: {
          rmc = prev.rmc.overrideAttrs (old: {
            nativeBuildInputs =
              (old.nativeBuildInputs or [ ]) ++ final.resolveBuildSystem { poetry-core = [ ]; };
          });
          rmscene = prev.rmscene.overrideAttrs (old: {
            nativeBuildInputs =
              (old.nativeBuildInputs or [ ]) ++ final.resolveBuildSystem { poetry-core = [ ]; };
          });

          # cairocffi (pulled in by rmc -> cairosvg) resolves libcairo at import
          # time with ctypes.util.find_library, which finds nothing inside the Nix
          # store. Rewrite the lookup to an absolute path, the same way nixpkgs'
          # own cairocffi package does.
          cairocffi = prev.cairocffi.overrideAttrs (old: {
            buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.cairo ];
            postInstall = (old.postInstall or "") + ''
              substituteInPlace $out/${python.sitePackages}/cairocffi/__init__.py \
                --replace-fail "'libcairo.so.2'" "'${pkgs.cairo}/lib/libcairo.so.2'"
            '';
          });
        };

        pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
            pyprojectOverrides
          ]
        );

        remarksBin = pythonSet.mkVirtualEnv "remarks-env" (
          workspace.deps.default // { remarks = [ "server" ]; }
        );

        runtimeLibs = [
          pkgs.stdenv.cc.cc.lib
          pkgs.zlib
          pkgs.cairo
          pkgs.glib
          pkgs.pango
          pkgs.gdk-pixbuf
          pkgs.libffi
        ];

        environment = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.uv
            pkgs.zotero
            pkgs.inotify-tools
            pkgs.gum

            # PDF utility tools
            # poppler's `pdfinfo` is great for reading pdf metadata
            pkgs.poppler-utils
            # qpdf is useful to modify pdf metadata
            pkgs.qpdf
          ]
          ++ runtimeLibs;

          env = {
            UV_PYTHON_DOWNLOADS = "never";
            UV_PYTHON = python.interpreter;
            LD_LIBRARY_PATH = lib.makeLibraryPath runtimeLibs;
          };

          shellHook = ''
            # Don't leak Nix python paths into the uv-managed .venv
            unset PYTHONPATH

            if ! [[ -f .githooks/pre-commit ]]; then
              git config core.hooksPath .githooks
            fi

            echo "🔍 Remarks Development Environment"
            echo "Nix configured git hooks and uv manages the python environment for you :)"

            echo ""
            echo "To install dependencies:"
            echo "uv sync --all-extras --all-groups"

            echo ""
            echo "To run remarks:"
            echo "uv run python -m remarks {IN_FILE.rmn} {OUTPUT_LOCATION}"

            echo ""
            echo "To test remarks:"
            echo "uv run pytest -m \"not unfinished_feature\""
          '';
        };

        dockerBinary = pkgs.dockerTools.buildImage {
          name = "remarks-bin";
          config = {
            Entrypoint = [ "${remarksBin}/bin/remarks" ];
          };
        };
        dockerServer = pkgs.dockerTools.buildLayeredImage {
          name = "remarks-server";
          config = {
            Entrypoint = [ "${remarksBin}/bin/remarks-server" ];
          };
        };
      in
      {
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
      }
    );
}
