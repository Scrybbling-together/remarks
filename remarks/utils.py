import json
import pathlib
from functools import cache
from typing import Tuple, List

# reMarkable's device dimensions
RM_WIDTH = 1404
RM_HEIGHT = 1872

INSERTED_PAGE = -1


@cache
def read_meta_file(path, suffix=".metadata"):
    file = path.with_name(f"{path.stem}{suffix}")
    if not file.exists():
        return None
    data = json.loads(open(file).read())
    return data


def is_document(path):
    metadata = read_meta_file(path)
    return metadata["type"] == "DocumentType"


def get_document_filetype(path):
    content = read_meta_file(path, suffix=".content")
    return content["fileType"]


def get_visible_name(path):
    metadata = read_meta_file(path)
    return metadata["visibleName"]


def get_ui_path(path):
    metadata = read_meta_file(path)
    parent_filename = metadata["parent"]

    # Check the parent
    ui_path = pathlib.Path("")

    while parent_filename != "":
        # First get the total path of the parent
        parent_path = pathlib.Path(path.parent, metadata["parent"])

        # Get the meta data of this parent
        metadata = read_meta_file(parent_path)
        if not metadata:
            return pathlib.Path(".")

        parent_title = metadata["visibleName"]

        # These go in reverse order up to the top level
        ui_path = pathlib.Path(parent_title).joinpath(ui_path)

        # Get the parent of this one
        parent_filename = metadata["parent"]

    return ui_path


def construct_redirection_map(content: dict) -> List[int]:
    """
    Constructs a redirection map based on the .content file.

    Each page either has a 'redir' key or not.

    `Page['redir']['value']` represents the index a page would originally be at if inserted pages would not be counted.

    The "redir" key can be interpreted as "this page is *redirected from* page n from the original source pdf".

    Args:
        content (dict): The content to construct the redirection map from.

    Example:
        The following dictionary represents a notebook based on a pdf. This pdf originally had two pages and has two inserted pages right after the first page.

        .. code-block::
            {
              'pages': [
                {
                  'uuid': 'a7d2b8',
                  'redir': {
                    'value': 0
                  }
                },
                {
                  'uuid': '8d26bb'
                },
                {
                  'uuid': '8d26bb'
                },
                {
                  'uuid': 'c736d9',
                  'redir': {
                    'value': 1
                  }
                }
              ]
            }
    """

    redirection_map = []
    if "cPages" in content:
        for i, page in enumerate(content['cPages']['pages']):
            if "redir" in page:
                redirection_map.append(page['redir']['value'])
            else:
                redirection_map.append(INSERTED_PAGE)
    return redirection_map


def is_inserted_page(idx: int) -> bool:
    return idx == INSERTED_PAGE


def get_document_tags(path: str):
    content = read_meta_file(path, suffix=".content")
    if "tags" in content:
        for tag in content['tags']:
            yield tag['name']

def get_pages_data(path: str) -> Tuple[List[str], List[int]]:
    content = read_meta_file(path, suffix=".content")
    redirection_map = construct_redirection_map(content)
    if "cPages" in content:
        return [page["id"] for page in content["cPages"]["pages"] if not page.get("deleted", {
            "value": 0})["value"] == 1], redirection_map
    return content["pages"], redirection_map


def list_ann_rm_files(path):
    content_dir = pathlib.Path(f"{path.parents[0]}/{path.stem}/")
    if not content_dir.is_dir():
        return []
    return list(content_dir.glob("*.rm"))
