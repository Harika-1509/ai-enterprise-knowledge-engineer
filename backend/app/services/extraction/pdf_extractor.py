from pathlib import Path

from pypdf import PdfReader

from app.services.extraction.base_extractor import BaseExtractor, ExtractedChunk


class PDFExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[ExtractedChunk]:
        reader = PdfReader(str(file_path))
        chunks: list[ExtractedChunk] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                chunks.append(
                    ExtractedChunk(
                        content=text,
                        metadata={"page_number": page_number, "source_type": "pdf"},
                    )
                )
        return chunks