from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Position:
    x: int
    y: int
    width: int
    height: int

@dataclass
class TextBlock:
    text: str
    confidence: float
    block_num: int
    line_num: Optional[int] = None
    position: Optional[Position] = None

@dataclass
class PageDimensions:
    width: int
    height: int

@dataclass
class Content:
    text_blocks: List[TextBlock]
    page_dimensions: Optional[PageDimensions] = None

@dataclass
class ProcessingInfo:
    method: str  # 'direct_extraction', 'ocr', or 'failed'
    searchable: bool
    timestamp: datetime = datetime.now()
    lang: Optional[str] = None
    ocr_engine: Optional[str] = None
    error_type: Optional[str] = None

@dataclass
class PDFPageResult:
    filename: str
    page_number: int
    content: Content
    processing_info: ProcessingInfo
    error: Optional[str] = None
    metadata: Optional[dict] = None
