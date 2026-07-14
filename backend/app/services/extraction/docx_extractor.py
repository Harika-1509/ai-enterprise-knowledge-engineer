from pathlib import Path

from docx import Document as DocxDocument

from app.services.extraction.base_extractor import BaseExtractor, ExtractedChunk


class DOCXExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> list[ExtractedChunk]:
        doc = DocxDocument(str(file_path))
        chunks: list[ExtractedChunk] = []

        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if text:
                chunks.append(
                    ExtractedChunk(
                        content=text,
                        metadata={"paragraph_index": i, "source_type": "docx"},
                    )
                )

        # Tables - pair header row with each subsequent row so chunks are
        # self-describing (mirrors XLSXExtractor's approach from Step 8).
        for t_idx, table in enumerate(doc.tables):
            rows = table.rows
            if not rows:
                continue

            header = [cell.text.strip() for cell in rows[0].cells]

            for r_idx, row in enumerate(rows[1:], start=1):
                values = [cell.text.strip() for cell in row.cells]
                pairs = [(h, v) for h, v in zip(header, values) if h and v]
                if not pairs:
                    continue
                # Verbalize as a natural sentence instead of pipe-delimited
                # fields - embedding/reranking models are trained on prose
                # and score natural language far more reliably than
                # "Key: Value | Key: Value" formatting.
                row_text = ", ".join(f"{h} is {v}" for h, v in pairs) + "."
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
