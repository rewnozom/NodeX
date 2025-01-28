# pages/qframes/Utils/FileUtils.py

import os
import zipfile

def create_zip(zip_path: str, source_dir: str):
    """
    Creates a ZIP archive from the specified source directory.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file != os.path.basename(zip_path):  # Avoid including the zip file itself
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    print(f"Exported all code blocks to {zip_path}")
