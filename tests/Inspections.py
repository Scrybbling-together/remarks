from dataclasses import dataclass
from typing import Optional


@dataclass
class VisualInspection:
    question: str
    expected_content: Optional[str] = None
    expected_color: Optional[str] = None

@dataclass 
class NotebookInspection:
    notebook: str  # Reference to notebook fixture name
    page_num: int
    inspection: VisualInspection