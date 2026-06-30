# Expected Output Structure

For an uploaded file named `example-poll.pdf`, the zip should contain a folder named `example-poll/`.

```text
example-poll/
├── manifest.json
├── report_text.md
├── report_tables.xlsx
├── report_raw.json
├── tables_csv/
│   ├── p001_t001.csv
│   ├── p001_t002.csv
│   └── p002_t001.csv
└── page_images/
    ├── page_001.png
    └── page_002.png
```

If no tables are detected, `tables_csv/` should still exist and `report_tables.xlsx` should still contain a `Table_Index` sheet with the expected headers.

## `manifest.json`

Required keys:

- `original_filename`
- `extraction_timestamp`
- `output_files_created`
- `page_image_files`
- `total_page_count`
- `total_extracted_tables`
- `warnings`
- `errors`

## `report_text.md`

Required content:

- Source filename
- Page count
- One `## Page X` heading per extracted page
- Raw extracted page text under each page heading

## `report_raw.json`

Required top-level keys:

- `source_filename`
- `page_count`
- `extraction_timestamp`
- `tool_version`
- `pages`

Each page object should include:

- `page_number`
- `page_image_filename`
- `extracted_page_text`
- `tables_found`
- `tables`

Each table object should include:

- `table_id`
- `page_number`
- `table_number_on_page`
- `row_count`
- `column_count`
- `csv_filename`
- `notes`
- `rows`

## `report_tables.xlsx`

The workbook must contain a `Table_Index` sheet with these columns:

- `table_id`
- `page_number`
- `table_number_on_page`
- `row_count`
- `column_count`
- `csv_filename`
- `notes`
