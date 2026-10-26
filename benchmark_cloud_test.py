import json
import shutil
import time
from pathlib import Path
from pylibrm_lines import SceneTree, Renderer, FailedToBuildTree

from rm_api.models import LocalDocument

from remarks import run_remarks

download_dir = Path(__file__).parent / "tests" / "in" / "cloud_download"
output_dir = Path(__file__).parent / "tests" / "out" / "cloud_download"
results_dir = Path(__file__).parent / "tests" / "out" / "cloud_download_results"
results_dir.mkdir(parents=True, exist_ok=True)

load_doc_times = {}
load_rm_times = {}
load_rm_times_individual = {}
process_times = {}
line_counts = {}
line_counts_individual = {}
errored_files = []

for file in download_dir.iterdir():
    start = time.time()
    doc = LocalDocument.load_rmdoc(file)
    load_doc_times[doc.uuid] = time.time() - start
    _load_rm_times = {}
    _line_counts = {}
    print(f"Handling {doc.metadata.visible_name}")
    for i, page in enumerate(doc.content.c_pages.pages, 1):
        print(f"Handling page {i}/{len(doc.content.c_pages.pages)}", end="\r")
        start = time.time()
        try:
            tree = SceneTree.from_document(doc, page.id)
        except FileNotFoundError:  # No lines file for page
            continue
        except FailedToBuildTree:
            errored_files.append(f"{file}/{page.id}")
            continue
        renderer: Renderer = tree.renderer
        _load_rm_times[f"{doc.uuid}/{page.id}"] = time.time() - start
        _line_counts[f"{doc.uuid}/{page.id}"] = 0
        for layer in renderer.layers:
            _line_counts[f"{doc.uuid}/{page.id}"] += len(layer.lines)

        del renderer
        del tree
    total_time = sum(_load_rm_times.values())
    total_line_count = sum(_line_counts.values())

    load_rm_times[doc.uuid] = total_time
    line_counts[doc.uuid] = total_line_count

    load_rm_times_individual.update(_load_rm_times)
    line_counts_individual.update(_line_counts)

    print("Running remarks......")
    start = time.time()
    run_remarks(file, output_dir)
    process_times[doc.uuid] = time.time() - start
    if output_dir.exists():
        shutil.rmtree(output_dir)
    else:
        errored_files.append(f"{file}/WHOLE_DOCUMENT")


def save_as_json(name, dictionary):
    with open(name, "w") as f:
        json.dump(dictionary, f)


save_as_json(results_dir / "load_doc_times", load_doc_times)
save_as_json(results_dir / "load_rm_times", load_rm_times)
save_as_json(results_dir / "load_rm_times_individual", load_rm_times_individual)
save_as_json(results_dir / "process_times", process_times)
save_as_json(results_dir / "line_counts", line_counts)
save_as_json(results_dir / "line_counts_individual", line_counts_individual)
save_as_json(results_dir / "errored_files", errored_files)

print("load_doc_times:", sum(load_doc_times) / len(load_doc_times))
print("load_rm_times:", sum(load_rm_times) / len(load_rm_times))
# print("load_rm_times_individual:", sum(load_rm_times_individual) / len(load_rm_times_individual))
print("process_times:", sum(process_times) / len(process_times))
print("line_counts:", sum(line_counts) / len(line_counts))
# print("line_counts_individual:", sum(line_counts_individual) / len(line_counts_individual))
