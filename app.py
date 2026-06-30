from __future__ import annotations
import streamlit as st

from exporters.export_bundle import build_export_zip
from extractors.pdf_extractor import ExtractionResult, extract_pdf_report


st.set_page_config(page_title="Pollster Raw Extraction Console", layout="wide")


def rows_for_preview(rows: list[list[str]]) -> list[dict[str, str]]:
    column_count = max((len(row) for row in rows), default=0)
    columns = [f"Column {index}" for index in range(1, column_count + 1)]

    return [
        {
            column: row[index] if index < len(row) else ""
            for index, column in enumerate(columns)
        }
        for row in rows
    ]


def render_result_preview(result: ExtractionResult) -> None:
    st.subheader(result.source_filename)

    total_tables = result.total_tables
    page_metric, table_metric = st.columns(2)
    page_metric.metric("Pages", result.page_count)
    table_metric.metric("Tables found", total_tables)

    if result.warnings:
        with st.expander("Warnings", expanded=False):
            for warning in result.warnings:
                st.warning(warning)

    if result.errors:
        with st.expander("Errors", expanded=True):
            for error in result.errors:
                st.error(error)

    for page in result.pages:
        with st.expander(f"Page {page.page_number} text", expanded=False):
            st.text(page.text.strip() or "No text extracted.")

    table_count = 0
    for page in result.pages:
        for table in page.tables:
            table_count += 1
            with st.expander(
                f"Table {table.table_id} - page {table.page_number}",
                expanded=table_count == 1,
            ):
                if table.rows:
                    st.dataframe(rows_for_preview(table.rows), width="stretch")
                else:
                    st.info("Empty table detected.")


def run_extraction(uploaded_files: list) -> tuple[list[ExtractionResult], bytes]:
    results: list[ExtractionResult] = []

    progress = st.progress(0, text="Extracting reports")
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        pdf_bytes = uploaded_file.getvalue()
        results.append(
            extract_pdf_report(
                pdf_bytes=pdf_bytes,
                source_filename=uploaded_file.name,
            )
        )
        progress.progress(index / len(uploaded_files), text=f"Extracted {uploaded_file.name}")

    progress.empty()
    zip_bytes = build_export_zip(results)
    return results, zip_bytes


def main() -> None:
    st.title("Pollster Raw Extraction Console")

    uploaded_files = st.file_uploader(
        "PDF reports",
        type=["pdf"],
        accept_multiple_files=True,
    )

    extract_clicked = st.button(
        "Extract reports",
        type="primary",
        disabled=not uploaded_files,
    )

    if extract_clicked and uploaded_files:
        with st.spinner("Extracting reports"):
            results, zip_bytes = run_extraction(uploaded_files)
            st.session_state["extraction_results"] = results
            st.session_state["extraction_zip"] = zip_bytes

    results = st.session_state.get("extraction_results")
    zip_bytes = st.session_state.get("extraction_zip")

    if results:
        st.divider()
        for result in results:
            render_result_preview(result)

        st.download_button(
            "Download extraction zip",
            data=zip_bytes,
            file_name="pollster_raw_extractions.zip",
            mime="application/zip",
            type="primary",
        )


if __name__ == "__main__":
    main()
