from typing import Optional

from core.common_imports import dataclass

@dataclass
class ExtractionConfig:
    key: str
    label: str
    description: str
    jql: str