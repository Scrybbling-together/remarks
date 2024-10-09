with import <nixpkgs> {};
let
  pythonEnv = pkgs.python310.withPackages (ps: with ps; [
    # Add any Python packages you need here
  ]);

  shellHookScript = ''
    #!/usr/bin/bash
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.libgcc.lib
      pkgs.zlib
    ]}:$LD_LIBRARY_PATH"

    echo "Setting up Git hooks"
    git config core.hooksPath .githooks

    if ! [[ -d .venv ]]; then
      ${pythonEnv}/bin/python -m venv .venv
      # shellcheck disable=SC1091
      source .venv/bin/activate
      pip install poetry
      poetry install
    else
      # shellcheck disable=SC1091
      source .venv/bin/activate
    fi
  '';

  shellHookChecked = pkgs.runCommand "shell-hook-checked" {
    buildInputs = [ pkgs.shellcheck ];
  } ''
    echo "${shellHookScript}" > shellhook.sh
    shellcheck shellhook.sh
    mkdir -p $out
    cp shellhook.sh $out/
  '';
in
pkgs.mkShell {
  buildInputs = [
    pythonEnv
    pkgs.poetry
    pkgs.zlib
    pkgs.gnumake
    pkgs.libgcc.lib
    pkgs.inotify-tools.out
  ];

  shellHook = builtins.readFile "${shellHookChecked}/shellhook.sh";
}