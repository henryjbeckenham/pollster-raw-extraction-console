# Pollster Raw Extraction Console

Browser-based Streamlit tool for extracting raw page text and detected tables from political polling PDF reports.

The console does not interpret polling data, classify results, create database rows, connect to Google Sheets, or run OCR. It preserves raw extracted text and tables with page numbers and stable table IDs.

## Repository layout

```text
.
├── app.py
├── extractors/
│   └── pdf_extractor.py
├── exporters/
│   └── export_bundle.py
├── utils/
│   └── file_naming.py
├── tests/
│   └── sample_expected_structure.md
├── README.md
└── requirements.txt
```

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud deployment

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app from the repository.
3. Set the main file path to `app.py`.
4. Deploy.

After deployment, ordinary operation happens in the browser: upload PDFs, click `Extract reports`, preview the extraction, and download the zip bundle.

## Output structure

The downloaded zip contains one folder per uploaded PDF. Each report folder contains:

```text
manifest.json
report_text.md
chatgpt_review.md
report_tables.xlsx
report_raw.json
tables_csv/
page_images/
```

`chatgpt_review.md` is a review-friendly Markdown file with page image filenames, table IDs, page text, and basic Markdown renderings of detected tables.

Each detected table is saved as `tables_csv/<table_id>.csv`, where table IDs use the format `p001_t001`, `p001_t002`, `p002_t001`, and so on.

Each page is also rendered as a PNG in `page_images/` using filenames such as `page_001.png`, `page_002.png`, and `page_003.png`. These rendered page images support visual verification for chart-heavy reports where table extraction may be incomplete.

`report_tables.xlsx` includes a `Table_Index` sheet with:

- `table_id`
- `page_number`
- `table_number_on_page`
- `row_count`
- `column_count`
- `csv_filename`
- `notes`

## Extraction behavior

- Page text is extracted with PyMuPDF.
- Page images are rendered with PyMuPDF.
- Tables are extracted with pdfplumber.
- Page numbers are preserved.
- Uploads are processed in memory and temporary files are removed after the zip is built.
- No uploaded PDF is stored permanently by the application code.
