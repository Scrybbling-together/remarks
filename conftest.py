import glob
import os

def cleanup_output_folder():
    """Remove all .md and .pdf files from the tests/out folder."""
    for file_pattern in ['tests/out/*.md', 'tests/out/*.pdf']:
        for file in glob.glob(file_pattern):
            os.remove(file)

def pytest_exception_interact(node, call, report):
    """It would be cool to catch snapshot errors here and show an image diff viewer popup with the before and after"""
    # if report.failed:
    #     with open('report.txt', 'w+') as f:
    #         f.write(report)

def pytest_sessionstart(session):
    cleanup_output_folder()