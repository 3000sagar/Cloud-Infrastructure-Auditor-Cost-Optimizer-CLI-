"""Entry point for `python -m cloud_auditor` and for PyInstaller packaging."""
from cloud_auditor.cli import app

if __name__ == "__main__":
    app()