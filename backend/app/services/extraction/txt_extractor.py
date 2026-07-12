from pathlib import Path

from app.services.extraction.base_extractor import BaseExtractor, ExtractedChunk


class TXTExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[ExtractedChunk]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            return []
        return [ExtractedChunk(content=text.strip(), metadata={"source_type": "txt"})]