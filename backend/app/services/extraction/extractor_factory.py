from app.models.document import FileType
from app.services.extraction.base_extractor import BaseExtractor
from app.services.extraction.docx_extractor import DOCXExtractor
from app.services.extraction.pdf_extractor import PDFExtractor
from app.services.extraction.pptx_extractor import PPTXExtractor
from app.services.extraction.txt_extractor import TXTExtractor
from app.services.extraction.xlsx_extractor import XLSXExtractor


class ExtractorFactory:
    """
    Factory Pattern: hides the mapping of file_type -> extractor class
    from the rest of the app. Callers just say 'give me the right
    extractor for this document' without a chain of if/elif checks.
    """

    _registry: dict[FileType, type[BaseExtractor]] = {
        FileType.PDF: PDFExtractor,
        FileType.DOCX: DOCXExtractor,
        FileType.PPTX: PPTXExtractor,
        FileType.XLSX: XLSXExtractor,
        FileType.TXT: TXTExtractor,
    }

    @classmethod
    def get_extractor(cls, file_type: FileType) -> BaseExtractor:
        extractor_class = cls._registry.get(file_type)
        if extractor_class is None:
            raise ValueError(f"No extractor registered for file type: {file_type}")
        return extractor_class()