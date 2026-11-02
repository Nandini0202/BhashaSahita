"""
Packages the complete BHASHA SAHITA project into deliverables:
- C:/Users/DELL/Downloads/bhasha-sahita-complete.zip
- C:/Users/DELL/Downloads/bhasha-sahita-final.zip
"""
import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path("C:/Users/DELL/Downloads")

EXCLUDE_DIRS = {".pytest_cache", "__pycache__", ".git", ".idea", ".vscode", ".venv", "venv", "env"}
EXCLUDE_EXTS = {".pyc", ".pyo"}

def create_archive(zip_path: Path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(BASE_DIR)
                archive_name = Path("bhasha-sahita") / rel_path
                zf.write(file_path, archive_name)
    print(f"Created archive: {zip_path} ({zip_path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    complete_zip = OUTPUT_DIR / "bhasha-sahita-complete.zip"
    final_zip = OUTPUT_DIR / "bhasha-sahita-final.zip"
    create_archive(complete_zip)
    create_archive(final_zip)
