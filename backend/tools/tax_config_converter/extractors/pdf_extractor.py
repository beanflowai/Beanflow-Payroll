"""
PDF Text Extractor for CRA T4127 Documents

Extracts text from T4127 PDF with page boundaries and table section chunking.
Uses PyMuPDF (fitz) for efficient text extraction.
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PDFMetadata:
    """Metadata extracted from T4127 PDF."""
    edition: str = ""
    edition_number: int = 0
    effective_date: str = ""
    year: int = 0
    total_pages: int = 0


@dataclass
class TableSection:
    """Represents a table section from the PDF."""
    table_id: str  # e.g., "8.1", "8.3"
    title: str
    content: str
    start_page: int
    end_page: int


@dataclass
class PDFContent:
    """Complete extracted content from T4127 PDF."""
    metadata: PDFMetadata
    full_text: str
    pages: list[str] = field(default_factory=list)
    tables: dict[str, TableSection] = field(default_factory=dict)


class PDFExtractor:
    """
    Extract text and tables from CRA T4127 PDF documents.

    Usage:
        extractor = PDFExtractor()
        content = extractor.extract("path/to/t4127.pdf")
        print(content.metadata.edition)
        print(content.tables["8.1"].content)
    """

    # Table patterns in Chapter 8
    # Note: 8.8 is used as a boundary marker for 8.7 (not saved to output)
    TABLE_PATTERNS = {
        "8.1": r"Table\s*8\.1[^0-9]",
        "8.2": r"Table\s*8\.2[^0-9]",
        "8.3": r"Table\s*8\.3[^0-9]",
        "8.4": r"Table\s*8\.4[^0-9]",
        "8.5": r"Table\s*8\.5[^0-9]",
        "8.6": r"Table\s*8\.6[^0-9]",
        "8.7": r"Table\s*8\.7[^0-9]",
        "8.8": r"Table\s*8\.8[^0-9]",  # Boundary marker for 8.7 (claim codes start here)
    }

    # Tables to actually save (8.8+ are boundary markers only)
    TABLES_TO_SAVE = {"8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7"}

    def __init__(self) -> None:
        self._fitz = None

    def _get_fitz(self):
        """Lazy import of PyMuPDF."""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                raise ImportError(
                    "PyMuPDF is required. Install with: uv add --optional tools PyMuPDF"
                )
        return self._fitz

    def extract(self, pdf_path: str | Path) -> PDFContent:
        """
        Extract full content from T4127 PDF.

        Args:
            pdf_path: Path to the T4127 PDF file

        Returns:
            PDFContent with metadata, full text, pages, and table sections
        """
        fitz = self._get_fitz()
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting content from: {pdf_path}")

        doc = fitz.open(pdf_path)
        try:
            # Extract all pages
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages.append(text)

            full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages)

            # Extract metadata from first page
            metadata = self._extract_metadata(pages[0] if pages else "", len(doc))

            # Find and extract table sections
            tables = self._extract_tables(pages, full_text)

            logger.info(
                f"Extracted {len(pages)} pages, {len(tables)} tables, "
                f"edition: {metadata.edition}"
            )

            return PDFContent(
                metadata=metadata,
                full_text=full_text,
                pages=pages,
                tables=tables
            )
        finally:
            doc.close()

    def _extract_metadata(self, first_page: str, total_pages: int) -> PDFMetadata:
        """Extract metadata from the first page of the PDF."""
        metadata = PDFMetadata(total_pages=total_pages)

        # Extract edition number (e.g., "120th Edition", "121st Edition")
        edition_match = re.search(r"(\d+)(?:st|nd|rd|th)\s+Edition", first_page, re.IGNORECASE)
        if edition_match:
            metadata.edition_number = int(edition_match.group(1))
            metadata.edition = f"{metadata.edition_number}th Edition"

        # Extract effective date (e.g., "January 1, 2025", "July 1, 2025")
        date_match = re.search(
            r"(January|July|February|March|April|May|June|August|September|October|November|December)\s+\d{1,2},?\s+(\d{4})",
            first_page,
            re.IGNORECASE
        )
        if date_match:
            month = date_match.group(1).lower()
            year = int(date_match.group(2))
            metadata.year = year

            # Convert to ISO format
            month_num = {
                "january": "01", "february": "02", "march": "03", "april": "04",
                "may": "05", "june": "06", "july": "07", "august": "08",
                "september": "09", "october": "10", "november": "11", "december": "12"
            }.get(month, "01")

            metadata.effective_date = f"{year}-{month_num}-01"

        return metadata

    def _extract_tables(
        self, pages: list[str], full_text: str
    ) -> dict[str, TableSection]:
        """Extract table sections from Chapter 8.

        Only saves tables in TABLES_TO_SAVE. Other tables (8.8+) are used as
        boundary markers but not included in output.
        """
        tables: dict[str, TableSection] = {}

        # Find all table positions in full text
        table_positions: list[tuple[str, int, int]] = []  # (table_id, position, page)

        for table_id, pattern in self.TABLE_PATTERNS.items():
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                # Calculate which page this is on
                text_before = full_text[:match.start()]
                page_num = text_before.count("--- PAGE BREAK ---")
                table_positions.append((table_id, match.start(), page_num))

        # Sort by position
        table_positions.sort(key=lambda x: x[1])

        # Extract content between tables
        for i, (table_id, start_pos, start_page) in enumerate(table_positions):
            # Skip tables not in TABLES_TO_SAVE (boundary markers only)
            if table_id not in self.TABLES_TO_SAVE:
                continue

            # End position is start of next table or end of document
            if i + 1 < len(table_positions):
                end_pos = table_positions[i + 1][1]
                end_page = table_positions[i + 1][2]
            else:
                end_pos = len(full_text)
                end_page = len(pages) - 1

            content = full_text[start_pos:end_pos].strip()

            # Extract title from content
            title_match = re.search(
                rf"Table\s*{re.escape(table_id)}\s*[–\-:]*\s*([^\n]+)",
                content,
                re.IGNORECASE
            )
            title = title_match.group(1).strip() if title_match else f"Table {table_id}"

            tables[table_id] = TableSection(
                table_id=table_id,
                title=title,
                content=content,
                start_page=start_page,
                end_page=end_page
            )

            logger.debug(
                f"Found Table {table_id}: '{title[:50]}...' "
                f"(pages {start_page}-{end_page}, {len(content)} chars)"
            )

        return tables

    def extract_chapter_8(self, pdf_path: str | Path) -> str:
        """
        Extract only Chapter 8 content from the PDF.

        Chapter 8 contains all the tax tables needed for payroll calculations.

        Args:
            pdf_path: Path to the T4127 PDF file

        Returns:
            Text content of Chapter 8
        """
        content = self.extract(pdf_path)
        return self.extract_chapter_8_from_text(content.full_text, content.tables)

    def extract_chapter_8_from_text(
        self,
        full_text: str,
        tables: dict[str, TableSection] | None = None
    ) -> str:
        """
        Extract Chapter 8 content from already extracted text.

        Args:
            full_text: Full text content from PDF
            tables: Optional dict of extracted table sections

        Returns:
            Text content of Chapter 8
        """
        # Find Chapter 8 start
        chapter_8_match = re.search(
            r"Chapter\s*8[^0-9]",
            full_text,
            re.IGNORECASE
        )

        if chapter_8_match:
            # Return from Chapter 8 to end
            return full_text[chapter_8_match.start():]

        # If no Chapter 8 marker, return tables content
        if tables:
            return "\n\n".join(t.content for t in tables.values())

        # Fallback: return last third of document (where tables typically are)
        third = len(full_text) // 3
        return full_text[-third:]

    def get_table_for_extraction(
        self, pdf_path: str | Path, table_ids: list[str]
    ) -> str:
        """
        Get specific tables for extraction.

        Args:
            pdf_path: Path to the T4127 PDF
            table_ids: List of table IDs to extract (e.g., ["8.1", "8.2"])

        Returns:
            Combined text content of specified tables
        """
        content = self.extract(pdf_path)

        result_parts = []
        for table_id in table_ids:
            if table_id in content.tables:
                result_parts.append(content.tables[table_id].content)
            else:
                logger.warning(f"Table {table_id} not found in PDF")

        return "\n\n".join(result_parts)
