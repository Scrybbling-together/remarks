import functools
import os
import tempfile

import pytest
from syrupy.extensions.single_file import SingleFileSnapshotExtension
import remarks

default_args = {"combined_pdf": True}


class JPEGImageExtension(SingleFileSnapshotExtension):
    _file_extension = "jpg"


def run_once(func):
    """Decorator to run a function only once."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


def with_remarks(input_name):
    """Decorator to run remarks for a specific input directory."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            input_dir = input_name
            output_dir = "tests/out"

            # Run remarks if it hasn't been run for this input directory
            if not getattr(with_remarks, f"run_{input_name}", False):
                remarks.run_remarks(input_dir, output_dir, **default_args)
                setattr(with_remarks, f"run_{input_name}", True)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(JPEGImageExtension)


def snapshot_test_pdf(filename: str, snapshot):
    """Snapshots a pdf by converting all pages to jpeg images and collecting their hashes.
    Makes a snapshot for each page"""
    assert os.path.isfile(f"tests/out/{filename}")
    with tempfile.TemporaryDirectory() as tempDir:
        os.system(f'convert -density 150 "tests/out/{filename}" -quality 100 {tempDir}/output-%3d.jpg')
        page_images = os.listdir(tempDir)
        for i, image in enumerate(page_images):
            name = f"{filename}:page-{i}"
            with open(f"{tempDir}/{image}", "rb") as f:
                assert f.read() == snapshot(name=name)
