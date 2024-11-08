# Claims Reader

## Purpose and Usage

This Python FastHTML based webapp is designed to extract billing information from scanned NYC EI Program Service Logs.

Conversion is done through HIPAA-compliant Azure Document Intelligence prebuilt-layout model to run OCR on the scanned pages.

Resulting text is de-identified, formatting and inferring blanks and errors are handled by Anthropic API.

Data is then stored to PostgreSQL to be fed into the Service Logging bot.

## Current Issues

- Fix Tables extraction to enable multi-page entries
    - iterate through all Tables
    - look for "Service Authorization" in cell contents
        - if found, extract Service Authorization number
    - Look for "Date of Service" in cell contents,
        - if found, extract full table

## Roadmap

- Upload pdf -> Convert -> Queue for billing
- Once all pdf's are queued, go to queue
- Select all entries that you want to bill, there will be a table with checkboxes for selection.
- download the file with the proper additional columns
- (long term- interface this with EI-Hub entry directly)

