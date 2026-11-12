#!/bin/sh
# Regenerates the vectors with the Rust edm-hash: EDM_HASH=path/to/edm-hash ./gen.sh
set -e
H=${EDM_HASH:-edm-hash}
cd "$(dirname "$0")"
"$H" table.csv -o default.csv --key-file key.hex
"$H" table.csv -o purview_cols.csv --key-file key.hex --purview-col "id:ignored=-" \
  --purview-col "email:case" --purview-col "name:case:ignored=-'"
"$H" table.csv -o wb_python.csv --key-file key.hex --tokenizer wb --lower python
"$H" table.csv -o wb_simple.csv --key-file key.hex --tokenizer wb
"$H" table.csv -o empty_cells.csv --key-file key.hex --allow-empty-cells
"$H" table.csv -o no_shapes.csv --key-file key.hex --allow-empty-cells --no-shapes
