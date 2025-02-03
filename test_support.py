import functools
import shutil

import remarks
from NotebookMetadata import NotebookMetadata
from fitz import Document


def with_remarks(metadata: NotebookMetadata):
    """Decorator to run remarks for a specific input directory."""
    input_name = metadata.rmn_source

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            input_dir = input_name
            output_dir = "tests/out"

            # Run remarks if it hasn't been run for this input directory
            if not getattr(with_remarks, f"run_{input_name}", False):
                remarks.run_remarks(input_dir, output_dir)
                setattr(with_remarks, f"run_{input_name}", True)

                remarks_generated_pdf = Document(f"tests/out/{metadata.notebook_name} _remarks.pdf")
                for file in metadata.rm_files:
                    if "photo" in file:
                        # show the photo next to the generated page
                        # - [ ] Get the generated page from the output
                        position = file["output_document_position"]
                        img_output = remarks_generated_pdf[position].get_pixmap()
                        img_output.save(f"tests/out/{metadata.notebook_name} - {position} - Remarks.jpg")
                        shutil.copy(file["photo"], f"tests/out/{metadata.notebook_name} - {position} - ReMarkable.jpg")


            return func(*args, **kwargs)

        return wrapper

    return decorator

