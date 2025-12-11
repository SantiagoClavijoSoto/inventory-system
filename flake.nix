{
  description = "Inventory System - POS and Inventory Management";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python312
            python312Packages.pip
            python312Packages.virtualenv

            # Build dependencies for mysqlclient
            pkg-config
            libmysqlclient

            # Node.js
            nodejs_22
            nodePackages.npm

            # Database tools
            mariadb

            # Development tools
            git
            jq
          ];

          shellHook = ''
            echo "🚀 Inventory System Development Environment"
            echo ""

            # Create virtual environment if it doesn't exist
            if [ ! -d "venv" ]; then
              echo "Creating virtual environment..."
              python3 -m venv venv
            fi

            # Activate virtual environment
            source venv/bin/activate

            # Install dependencies if not present
            if [ ! -f "venv/.installed" ]; then
              echo "Installing Python dependencies..."
              pip install -r backend/requirements.txt
              touch venv/.installed
            fi

            echo "Python: $(python3 --version)"
            echo "Node: $(node --version)"
            echo ""
            echo "📦 To start backend: cd backend && python manage.py runserver"
            echo "🎨 To start frontend: cd frontend && npm run dev"
            echo ""

            # Set database URL for local MariaDB (no password)
            export DATABASE_URL="mysql://root@localhost:3306/inventory_db"
          '';
        };
      }
    );
}
