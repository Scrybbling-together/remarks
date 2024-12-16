import glob
import os

def cleanup_output_folder():
    """Remove all .md and .pdf files from the tests/out folder."""
    for file_pattern in ['tests/out/*.md', 'tests/out/*.pdf']:
        for file in glob.glob(file_pattern):
            os.remove(file)

def pytest_sessionstart(session):
    cleanup_output_folder()