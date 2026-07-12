from pathlib import Path

from docx import Document as DocxDocument

from app.services.extraction.base_extractor import BaseExtractor, ExtractedChunk


class DOCXExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[ExtractedChunk]:
        doc = DocxDocument(str(file_path))
        chunks: list[ExtractedChunk] = []

        # Paragraphs
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if text:
                chunks.append(
                    ExtractedChunk(
                        content=text,
                        metadata={"paragraph_index": i, "source_type": "docx"},
                    )
                )

        # Tables - flattened row by row, since table structure matters for meaning
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip(" |"):
                    chunks.append(
                        ExtractedChunk(
                            content=row_text,
                            metadata={
                                "table_index": t_idx,
                                "row_index": r_idx,
                                "source_type": "docx_table",
                            },
                        )
                    )
        return chunks