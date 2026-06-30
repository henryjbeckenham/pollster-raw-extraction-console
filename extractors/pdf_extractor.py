from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import fitz
import pdfplumber


TOOL_VERSION = "0.1.0"
PAGE_IMAGE_DPI = 150


@dataclass
class ExtractedTable:
    table_id: str
    page_number: int
    table_number_on_page: int
    rows: list[list[str]]
    notes: str = ""

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        if not self.rows:
            return 0
        return max(len(row) for row in self.rows)

    @property
    def csv_filename(self) -> str:
        return f"{self.table_id}.csv"

    def to_raw_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "page_number": self.page_number,
            "table_number_on_page": self.table_number_on_page,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "csv_filename": self.csv_filename,
            "notes": self.notes,
            "rows": self.rows,
        }


@dataclass
class ExtractedPage:
    page_number: int
    text: str = ""
    tables: list[ExtractedTable] = field(default_factory=list)
    image_png: bytes = field(default=b"", repr=False)

    @property
    def page_image_filename(self) -> str:
        return f"page_images/page_{self.page_number:03d}.png"

    def to_raw_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "page_image_filename": self.page_image_filename,
            "extracted_page_text": self.text,
            "tables_found": len(self.tables),
            "tables": [table.to_raw_dict() for table in self.tables],
        }


@dataclass
class ExtractionResult:
    source_filename: str
    page_count: int
    extraction_timestamp: str
    tool_version: str
    pages: list[ExtractedPage]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_tables(self) -> int:
        return sum(len(page.tables) for page in self.pages)

    def to_raw_dict(self) -> dict[str, Any]:
        return {
            "source_filename": self.source_filename,
            "page_count": self.page_count,
            "extraction_timestamp": self.extraction_timestamp,
            "tool_version": self.tool_version,
            "pages": [page.to_raw_dict() for page in self.pages],
        }


def extract_pdf_report(
    pdf_bytes: bytes,
    source_filename: str,
    tool_version: str = TOOL_VERSION,
) -> ExtractionResult:
    extraction_timestamp = datetime.now(timezone.utc).isoformat()
    warnings: list[str] = []
    errors: list[str] = []

    pages, page_count = _extract_pages_with_pymupdf(pdf_bytes, warnings, errors)
    _extract_tables_with_pdfplumber(pdf_bytes, pages, warnings, errors)

    return ExtractionResult(
        source_filename=source_filename,
        page_count=page_count,
        extraction_timestamp=extraction_timestamp,
        tool_version=tool_version,
        pages=pages,
        warnings=warnings,
        errors=errors,
    )


def _extract_pages_with_pymupdf(
    pdf_bytes: bytes,
    warnings: list[str],
    errors: list[str],
) -> tuple[list[ExtractedPage], int]:
    pages: list[ExtractedPage] = []

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            page_count = document.page_count
            for page_index in range(page_count):
                page_number = page_index + 1
                try:
                    page = document.load_page(page_index)
                except Exception as exc:
                    warnings.append(
                        f"Could not load page {page_number} with PyMuPDF: {exc}"
                    )
                    pages.append(ExtractedPage(page_number=page_number))
                    continue

                try:
                    text = page.get_text("text")
                except Exception as exc:
                    text = ""
                    warnings.append(
                        f"Text extraction failed on page {page_number}: {exc}"
                    )

                try:
                    pixmap = page.get_pixmap(dpi=PAGE_IMAGE_DPI, alpha=False)
                    image_png = pixmap.tobytes("png")
                except Exception as exc:
                    image_png = b""
                    warnings.append(
                        f"Page image rendering failed on page {page_number}: {exc}"
                    )

                pages.append(
                    ExtractedPage(
                        page_number=page_number,
                        text=text,
                        image_png=image_png,
                    )
                )

            return pages, page_count
    except Exception as exc:
        errors.append(f"Could not open PDF with PyMuPDF: {exc}")
        return pages, 0


def _extract_tables_with_pdfplumber(
    pdf_bytes: bytes,
    pages: list[ExtractedPage],
    warnings: list[str],
    errors: list[str],
) -> None:
    page_lookup = {page.page_number: page for page in pages}

    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page_index, plumber_page in enumerate(pdf.pages, start=1):
                page = page_lookup.get(page_index)
                if page is None:
                    page = ExtractedPage(page_number=page_index)
                    pages.append(page)
                    page_lookup[page_index] = page

                try:
                    raw_tables = plumber_page.extract_tables() or []
                except Exception as exc:
                    warnings.append(
                        f"Table extraction failed on page {page_index}: {exc}"
                    )
                    continue

                for table_index, raw_table in enumerate(raw_tables, start=1):
                    table_id = f"p{page_index:03d}_t{table_index:03d}"
                    rows = _normalize_table_rows(raw_table)
                    notes = ""
                    if not rows:
                        notes = "No rows extracted by pdfplumber."

                    page.tables.append(
                        ExtractedTable(
                            table_id=table_id,
                            page_number=page_index,
                            table_number_on_page=table_index,
                            rows=rows,
                            notes=notes,
                        )
                    )
    except Exception as exc:
        errors.append(f"Could not open PDF with pdfplumber: {exc}")

    pages.sort(key=lambda page: page.page_number)


def _normalize_table_rows(raw_table: list[list[Any]] | None) -> list[list[str]]:
    if not raw_table:
        return []

    normalized_rows: list[list[str]] = []
    for row in raw_table:
        if row is None:
            normalized_rows.append([])
            continue

        normalized_rows.append(
            ["" if cell is None else str(cell) for cell in row]
        )

    return normalized_rows
