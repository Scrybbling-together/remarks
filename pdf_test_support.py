import subprocess
import shutil

from test_support import DevelopmentEnvironmentSetupException


def is_valid_pdf(pdf_path: str) -> bool:
    """
    Execute pdfinfo on the given PDF file and return the parsed output.

    Args:
        pdf_path: Path to the PDF file to analyze

    Returns:
        Whether the PDF is valid or not.

    Raises:
        PDFInfoError: If pdfinfo is not installed or fails to execute
        FileNotFoundError: If the PDF file doesn't exist
    """
    # First check if pdfinfo is available
    if not shutil.which('pdfinfo'):
        raise DevelopmentEnvironmentSetupException(
            "pdfinfo command not found. See README.md setup section for installation instructions."
        )

    try:
        # Execute pdfinfo and capture output
        result = subprocess.run(
            ['pdfinfo', pdf_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=1
        )

        return result.returncode == 0
    except FileNotFoundError as e:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}") from e
    except subprocess.CalledProcessError as e:
        raise DevelopmentEnvironmentSetupException(
            f"pdfinfo failed to process the file. Error: {e.stderr}"
        ) from e
