# EDMTool

`edmtool` is a command-line interface tool, written in Python, designed to interact with the Cyberhaven EDM DB API. It allows users to manage and upload hashed EDM database files to the Cyberhaven console. Once the data is ingested into the Cyberhaven backend, it can be operated on them further from within the Cyberhaven dashboard (e.g., for building EDM Rules and managing the database definitions).

Our tool supports both [Spooky Hash V2](https://en.wikipedia.org/wiki/Jenkins_hash_function#SpookyHash) and [SHA256](https://en.wikipedia.org/wiki/SHA-2).

## Table of Contents

- [Features](#features)
- [Development](#development)
- [Installation](#installation)
- [Usage](#usage)
  - [Hash EDM DB file](#hash-edm-db-file)
  - [Create a New Database Entry and Upload the EDM DB File](#create-a-new-database-entry-and-upload)
  - [Create a New Database Entry](#create-a-new-database-entry)
  - [Upload the EDM DB File](#upload-a-file)
  - [Update an existing Database Entry and Upload the EDM DB File](#update-an-existing-database-entry-and-upload)

## Features

- Hash EDM DB file into a compatible format in order to upload.
- Create a new EDM database entry and upload the EDM DB file directly.
- Upload EDM DB file with progress tracking.

## Development

For development, we recommend `Python>=3.7` and `pip`. Please also use `virtualenv` (or an alternative) in order to develop in isolation from the system-wide Python packages.

Once you install `virtualenv`, run:

```bash
make venv

# IMPORTANT!
# activate the venv
source .venv/bin/activate
```

To install all dependencies

```bash
make install-dev
```

Also it is possible to run the CLI for testing purposes without building and installing it locally:

```bash
python3 -m edmtool <commands>
```

## Installation

Build the package:

```bash
make build
```

To install after building (from the dist folder), you can use pip:

```bash
pip install ./dist/edmtool-<version>.tar.gz
```

or you can run the following to install locally:

```bash
make install-local
```

## Usage

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

The supported hashing algorithms are `spooky` and `sha256`.

### Create a new Database Entry and upload

Create an new EDM DB entry and upload the associated file.

```bash
edmtool create_and_upload --name "Your DB Name" --description "Your Description" --metadata_file_path /path/to/your/file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Update an existing Database Entry and upload

Update an existing EDM DB entry and upload the associated file.

```bash
edmtool update_and_upload --id DATABASE_ID --description "Your Description" --metadata_file_path /path/to/your/updated_file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Create a new Database entry

Create the database entry based on a generated EDM DB encoded file.

```bash
edmtool create --name "Your DB Name" --description "Your Description" --metadata_file_path /path/to/your/file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Update an existing Database entry

Update an existing database with a new EDM DB encoded file.

```bash
edmtool update --name "Your DB Name" --description "Your Description" --metadata_file_path /path/to/your/file_encoded_metadata.json --base_url http://example.cyberhaven.com --token YOUR_AUTH_TOKEN
```

### Upload an encoded file

Upload the EDM DB encoded file. This applies to both new and existing database entries.

```bash
edmtool upload --id DATABASE_ID --metadata_file_path ./path/to/your/file_encoded_metadata.json --base_url http://api.example.com --token YOUR_AUTH_TOKEN
```
