# EDMTool

`edmtool` is a command-line interface tool, written in Python, designed to interact with the Cyberhaven EDM DB API. It allows users to manage and upload hashed EDM database files to the Cyberhaven console. Once the data is ingested into the Cyberhaven backend, it can be operated on them further from within the Cyberhaven dashboard (e.g., for building EDM Rules and managing the database definitions).

Our tool supports [Spooky Hash V2](https://en.wikipedia.org/wiki/Jenkins_hash_function#SpookyHash) and [SHA256](https://en.wikipedia.org/wiki/SHA-2) (legacy formats), and keyed HMAC-SHA256 (`hmac-sha256`, the new EDM engine format).

## Table of Contents

- [Features](#features)
- [Development](#development)
- [Installation](#installation)
- [Usage](#usage)

  - [Hash EDM DB file](#hash-edm-db-file)
  - [Hash with a tenant key](#hash-with-a-tenant-key-hmac-sha256)
  - [Create a New Database Entry and Upload the EDM DB File](#create-a-new-database-entry-and-upload)
  - [Update a Existing Database Entry and Upload the EDM DB File](#update-an-existing-database-entry-and-upload)
  - [Create a New Database Entry (without uploading)](#create-a-new-database-entry-without-uploading)
  - [Update an Existing Database Entry (without uploading)](#update-an-existing-database-entry-without-uploading)
  - [Upload the EDM DB File manually](#upload-an-encoded-file)

## Features

- Hash EDM DB file into a compatible format in order to upload.
- Create a new EDM database entry and upload the EDM DB file directly.
- Upload EDM DB file with progress tracking.

## Considerations

If the original EDM DB file is malformed, the hashing process will not fail, but the malformed rows will be skipped. The tool will log the number of skipped rows and their positions.

## Development

For development, we recommend `Python>=3.7` and `pip`. Please also use `virtualenv` (or an alternative) in order to develop in isolation from the system-wide Python packages.

Once you install `virtualenv`, run:

```bash
make create_venv

# IMPORTANT!
# activate the venv
source .venv/bin/activate
```

To install all dependencies

```bash
make install-dev-deps
```

Also it is possible to run the CLI for testing purposes without building and installing it locally:

```bash
python3 -m edmtool <commands>
```

## Installation

After installing all dependencies, build the package:

```bash
make build
```

To install after building, you can use pip:

```bash
pip install ./dist/edmtool-<version>.tar.gz
```

or you can run the following to install the package from local code:

```bash
make install-local
```

## Usage

### Create API token

To use `edmtool`, you need to create an API token in the Cyberhaven console. The token is used to authenticate the tool with the Cyberhaven backend.

Open "Settings" > "API token management (legacy)" and create a new token. Copy the token and use it as `YOUR_AUTH_TOKEN` in the following commands.

### Hash EDM DB file

It takes an input file provided by you and generates 2 new output files.
A `<filename>_encoded.csv` and `<filename>_encoded_metadata.json`, please do not modify in any way or remove those once generated.

```bash
edmtool encode --algorithm "spooky" --db_file_path ./path/to/your/file.csv
```

You can also use optional argument to indicate that your EDM DB CSV file delimiter is distinct from `','`

```bash
--db_file_delimiter ';'
```

The supported hashing algorithms are `spooky`, `sha256` and `hmac-sha256` (see below).

If your EDM DB file contains empty cells (e.g., missing email or phone number), you can use the `--allow_empty_cells` flag to include those rows in the output. Without this flag, rows with empty cells are skipped.

```bash
edmtool encode --algorithm "sha256" --db_file_path ./path/to/your/file.csv --allow_empty_cells
```

Empty cells will be hashed but will never produce matches during evaluation.

### Hash with a tenant key (`hmac-sha256`)

`hmac-sha256` hashes every cell with HMAC-SHA256 under a per-tenant secret key, so the hashed file cannot be
brute-forced without the key. The output is the `edm` format read by the new EDM engine: a first line
`#edm-hashed {json}` (algorithm, `key_id`, lowercasing, per-column tokenization and value shapes), the header row,
then `n|base64(fingerprint)` cells.

```bash
edmtool encode --algo hmac-sha256 --key-file ./tenant.key --db_file_path ./path/to/your/file.csv
```

Key handling:

- Fetch the key from your secret manager at hash time (e.g. into a file readable only by you, or as hex in
  `$EDM_KEY_HEX` when `--key-file` is not given) and delete local copies afterwards.
- The key is hex in both `--key-file` and `$EDM_KEY_HEX`; surrounding whitespace is ignored. Keys must be at least
  32 bytes (64 hex digits), e.g. `openssl rand -hex 32 > tenant.key`.
- The key is never written to the output or uploaded. Only `key_id`, a one-way identifier
  (first 8 bytes of SHA-256("edm-key-id" + key), hex), is stored so a mismatched key is detected.
- Rotating the key requires re-hashing and re-uploading the database.

Tokenization options (`hmac-sha256` only):

- `--tokenizer purview` (default): split on space, tab, `,.;?!`, CR and LF, after NFKC normalization.
  `--tokenizer wb` uses the legacy split characters.
- `--purview-col NAME[:case][:ignored=CHARS]` (repeatable): `case` makes the column case sensitive, and
  `ignored` lists characters removed from its tokens (it goes last and may contain `:`), e.g. `--purview-col "ssn:ignored=-"` hashes
  `123-45-6789` as `123456789`.
- `--lower simple` (default) lowercases per code point, the same way documents are, so values with `İ` or a final
  `Σ` match. `--lower python` reproduces the legacy lowercasing.
- `--no-shapes` omits the per-column value shapes (word count, character classes, length, never the values).
  Without them the engine still matches the same, but scans slower because it cannot skip candidates.

`spooky` and `sha256` output is unchanged. The upload actions do not accept `hmac-sha256` databases yet.

### Create a new Database Entry and upload

Create an new EDM DB entry and upload the associated file. The file has to be hashed prior to creating the database entry.

```bash
edmtool create_and_upload --name "Your DB Name" --description "Your Description" --metadata_file_path /path/to/your/file_encoded_metadata.json --base_url https://your-tenant.cyberhaven.io --token YOUR_AUTH_TOKEN
```

### Update an existing Database Entry and upload

Update an existing EDM DB entry and upload updated associated file. The file has to be hashed prior to updating the database entry.

```bash
edmtool update_and_upload --id DATABASE_ID --description "Your Description" --metadata_file_path /path/to/your/updated_file_encoded_metadata.json --base_url https://your-tenant.cyberhaven.io --token YOUR_AUTH_TOKEN
```

### Create a new Database entry (without uploading)

Create the database entry based on a generated EDM DB encoded file. The file has to be hashed prior to creating the database entry.

```bash
edmtool create --name "Your DB Name" --description "Your Description" --metadata_file_path /path/to/your/file_encoded_metadata.json --base_url https://your-tenant.cyberhaven.io --token YOUR_AUTH_TOKEN
```

### Update an existing Database entry (without uploading)

Update an existing database with a new EDM DB encoded file.

```bash
edmtool update --name "Your DB Name" --description "Your Description" --metadata_file_path /path/to/your/file_encoded_metadata.json --base_url https://your-tenant.cyberhaven.io --token YOUR_AUTH_TOKEN
```

### Upload an encoded file

Upload the EDM DB encoded file. This applies to both new and existing database entries.

```bash
edmtool upload --id DATABASE_ID --metadata_file_path ./path/to/your/file_encoded_metadata.json --base_url https://your-tenant.cyberhaven.io --token YOUR_AUTH_TOKEN
```
