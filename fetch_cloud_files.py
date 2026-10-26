import json
import os
import threading
import time
import zipfile
from functools import partial
from pathlib import Path

from rm_api import API
from rm_api.defaults import FileTypes

from rm_api.models import Document

if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    config = {
    "uri": "https://webapp.cloud.remarkable.com/",
    "discovery_uri": "https://service-manager-production-dot-remarkable-production.appspot.com/",
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

api = API(
    uri=config["uri"],
    discovery_uri=config["discovery_uri"],
    token_file_path="token",
    sync_file_path="sync",
)
api.debug = True
docs = []


items = 0
last_update_time = 0
done = 0

def strip_name(filename: str):
    # Source - https://stackoverflow.com/a/7406369
    # Posted by Remi, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-10-25, License - CC BY-SA 4.0

    keepcharacters = (' ', '.', '_')
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()


def track_progress(items_done, items_total):
    global items, done, last_update_time
    items = items_total
    done = items_done
    last_update_time = time.time()

threading.Thread(
    target=api.get_documents, args=(track_progress,), daemon=True
).start()

while last_update_time <= 0:
    pass
while done < items:
    print(f"Downloading documents... {done}/{items}", end="\r")
print(f"Downloaded {items} documents")


download_dir = Path(__file__).parent / "tests" / "in" / "cloud_download"
os.makedirs(download_dir, exist_ok=True)
print("Making full downloads to tests/in")
total_docs = len(api.documents)
for i, document in enumerate(api.documents.values(), 1):
    document.ensure_download()

    while document.downloading:
        print(f"Downloading full document {document.metadata.visible_name} {i}/{total_docs}", end="\r")
        time.sleep(0.1)
    files_available = document.check_files_availability()
    pdf_is_there = document.content.file_type == FileTypes.Notebook.value or any(file.endswith(".pdf") for file in files_available)
    available = all(file in files_available.keys() for file in document.content_files)
    if not available or not pdf_is_there:
        print(f"Could not download {document.metadata.visible_name}")
        continue
    print(f"Exporting full document {document.metadata.visible_name} {i}/{total_docs}")

    filepath = download_dir / (strip_name(document.metadata.visible_name) + ".rmdoc")

    with zipfile.ZipFile(filepath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in document.files:
            zf.write(
                os.path.join(api.sync_file_path, file.hash), arcname=file.uuid
            )