# Python CSV Cleanup

A small command-line tool that cleans a CSV using explicit column rules and writes a JSON audit. It keeps conflicting records for review instead of choosing one automatically.

This is an original, self-initiated portfolio example. All sample records are fictional; the email addresses use example domains. It is not a previous client commission.

## Before and after

The input has surrounding spaces, inconsistent email casing, one duplicate, two different records with the same ID, and one record without an ID.

`sample-input.csv`:

```csv
id,company,email,status
0001, North Studio , TEAM@example.com , active 
0001,North Studio,team@example.com,active
0002,Oak Workshop,SALES@example.org,active
0002,Oak Workshop,hello@example.org,active
,Unassigned Office, office@example.net ,pending
```

With `--trim company,email,status --lowercase email --key id`, the result is:

`sample-cleaned.csv`:

```csv
id,company,email,status
0001,North Studio,team@example.com,active
0002,Oak Workshop,sales@example.org,active
0002,Oak Workshop,hello@example.org,active
,Unassigned Office,office@example.net,pending
```

The audit in `sample-audit.json` records **5 input rows, 4 output rows, 5 changed cells, and 1 removed duplicate**. It retains and flags the conflicting `0002` record and the record without an ID. Leading zeros in `0001` and `0002` are preserved.

## Run

Requires Python 3.10 or newer. It uses only the Python standard library; no package installation is needed.

From this directory:

```sh
python cleanup_csv.py sample-input.csv cleaned.csv --report audit.json --trim company,email,status --lowercase email --key id
```

Expected console output:

```text
5 input rows -> 4 output rows; 5 changed cells; 1 identical duplicates removed; 1 conflicting keys retained.
```

`cleaned.csv` and `audit.json` must be new filenames. The included `sample-cleaned.csv` and `sample-audit.json` are reference outputs. The tool refuses to overwrite an existing output or report, use the input as an output, or use the same path for both outputs.

Available rules:

| Argument | Behavior |
| --- | --- |
| `--trim company,email,status` | Removes leading and trailing whitespace only from the named columns. |
| `--lowercase email` | Lowercases only the named columns, after trimming where requested. |
| `--key id` | Groups records by one key column or a comma-separated list of key columns. Removes a later row only if all its fields match an earlier row after the selected rules have run. |

Without `--key`, no rows are deduplicated. Conflicting records with the same key stay in the output. Any record with an empty key field stays in the output and is flagged. Missing keys are assessed after the selected transformations, so add a key column to `--trim` if whitespace-only keys should count as empty.

## Audit and validation

The JSON report includes the selected rules, counts, each changed cell's before/after values, duplicate-to-retained record references, conflicting keys, and missing-key record references. Its `source_row` values count CSV records starting at 2, with the header counted as record 1; they are not physical line offsets for a quoted multiline field.

Validation rejects duplicate or empty column names, unknown columns in a rule, and records with too many or too few fields. Values remain strings: identifiers, dates, zero amounts and blank cells are not converted into numbers or inferred types.

## Verification already completed

The unchanged source and tests passed all **five unit tests** before this package was prepared:

1. Explicit transformations preserve identifiers and remove only identical rows, including repeated conflicting records.
2. Blank keys are retained and reported.
3. Quoted commas, embedded newlines and Unicode survive a round trip.
4. Invalid field counts, duplicate headers and unknown rule columns fail validation.
5. Zero amounts, blanks, date strings and formula-like text remain unchanged without a transformation rule.

To run these checks yourself:

```sh
python -m unittest -v test_cleanup_csv.py
```

A separate, previously completed check used **5,000 fictional rows and 20 columns**: it produced 4,999 rows after removing one exact duplicate, preserved IDs/dates/amounts, and completed in 0.225 seconds on the test machine. This is one observed run, not a performance guarantee. The large fixture is intentionally omitted from this minimal example.

## Boundaries

- UTF-8, comma-separated CSV with a header row. UTF-8 input with a byte-order mark is supported. Other delimiters, encodings and XLSX files are outside this example.
- No fuzzy matching, automatic conflict resolution, email deliverability checks, date conversion, OCR or external service calls.
- Formula-like text is preserved as data. The tool does not make untrusted CSV safe for execution in a spreadsheet application.
- Data is processed in memory. The output and report are created separately; they are not an atomic two-file transaction.
- The audit contains source values. The included audit is fictional; audits of client data should be handled as client data.

## Files

| File | Purpose |
| --- | --- |
| `cleanup_csv.py` | Command-line implementation and importable `clean_csv` function. |
| `test_cleanup_csv.py` | Five focused unit tests. |
| `sample-input.csv` | Small fictional input. |
| `sample-cleaned.csv` | Reference cleaned output. |
| `sample-audit.json` | Reference audit for the demonstrated rules. |
| `README.md` | Example, commands, verified behavior and scope. |
