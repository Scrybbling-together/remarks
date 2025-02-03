import functools
import remarks
from NotebookMetadata import NotebookMetadata


def run_once(func):
    """Decorator to run a function only once."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


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
            return func(*args, **kwargs)

        return wrapper

    return decorator


class DevelopmentEnvironmentSetupException(Exception):
    """Custom exception related to development environment not being set-up correctly.
       Please refer to the project documentation for more information."""
    pass
