{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
  ];

  idx = {
    extensions = [ "ms-python.python" ];

    workspace = {
      onCreate = {
        install = ''
          python -m venv .venv
          source .venv/bin/activate
          pip install --upgrade pip setuptools wheel
          pip install -r requirements.txt
          pip install faiss-cpu
          pip install --upgrade sentence-transformers
        '';
        default.openFiles = [ "README.md" "main.py" ];
      };
    };
 
    previews = {
      enable = true;
      previews = {
        web = {
          command = [ "./devserver.sh" ];
          env = { PORT = "$PORT"; };
          manager = "web";
        };
      };
    };
  };
}
