import os
import logging
import json

from datetime import datetime
from tqdm import tqdm

from edmtool.utils import Calculate_file_sha256_checksum, Get_file_size, Count_file_lines
from edmtool.hasher import Hasher
from edmtool.errors import CellIsEmptyError, EncodedFileExistsError, DifferentCellsInTheRowError


class FileTransformer:
    _encoded_delimiter = ','

    def __init__(self, hasher: Hasher, delimiter=',') -> None:
        self._delimiter = delimiter
        self._hasher = hasher

    # optional to develop in the future(?)
    def _create_new_file_encoded(self, path: str):
        directory, filename = os.path.split(path)
        new_filename = filename.split('.')[0] + '_encoded.csv'
        return os.path.join(directory, new_filename)

    def _create_new_file_metadata(self, path: str):
        directory, filename = os.path.split(path)
        new_filename = filename.split('.')[0] + '_metadata.json'
        return os.path.join(directory, new_filename)

    def _extract_file_name(self, path: str):
        _, filename = os.path.split(path)
        return filename.split('.')[0]

    def check_file_exists(self, path: str):
        return os.path.exists(path) and path.endswith('.csv')

    def _check_file_to_append(self, path: str):
        if not self.check_file_exists(path):
            return 0

        with open(path, 'r') as file:
            line_count = 0
            for _ in file:
                line_count += 1

        return line_count

    def create_encoded_file(self, file_path: str):
        encoded_file_path = self._create_new_file_encoded(file_path)
        if self.check_file_exists(encoded_file_path):
            raise EncodedFileExistsError(
                f"Encoded file exists under path {encoded_file_path}, please remove it first to proceed."
            )
        first_line = []
        counter = 0
        skipped_rows = 0

        try:
            with open(file_path, 'r') as src:
                cells_count = 0

                with tqdm(src,
                          total=Count_file_lines(file_path),
                          unit_scale=True,
                          desc=f"INFO: Hashing the file {file_path} with {self._hasher.algo}",
                          initial=0) as wrapped_file:

                    with open(encoded_file_path, 'w') as dst:
                        for line in wrapped_file:
                            skip_row = False
                            base_line = line.replace("\n", "")
                            cells = base_line.split(self._delimiter)

                            if counter == 0:
                                first_line = cells
                                cells_count = len(cells)
                                dst.write(','.join(cells))
                                counter += 1
                                continue

                            if len(cells) != cells_count:
                                counter += 1
                                skipped_rows += 1
                                logging.info(
                                    f"Row {counter} has {len(cells)} cells, but it should have {cells_count} cells, as indicated in the header. The row {counter} is skipped"
                                )
                                skip_row = True

                            for i in range(len(cells)):
                                if cells[i] != '':
                                    cells[i] = self._hasher.encode(cells[i])
                                else:
                                    counter += 1
                                    skipped_rows += 1
                                    logging.info(
                                        f"The row {counter} is malformed.\nCell {i} in the line {counter} is empty, remove the row or fill the cell with the relevant data. The row {counter} is skipped"
                                    )
                                    skip_row = True

                            if skip_row:
                                continue

                            if counter > 0:
                                dst.write('\n')

                            dst.write(",".join(cells))
                            counter += 1

        except Exception as e:
            # remove the corrupted file
            if os.path.exists(encoded_file_path):
                os.remove(encoded_file_path)
            raise e

        hash = Calculate_file_sha256_checksum(encoded_file_path)
        size = Get_file_size(encoded_file_path)

        metadata = {
            'filename': self._extract_file_name(encoded_file_path) + '.csv',
            'checksum': hash,
            'size': size,
            'algo': self._hasher.algo,
            'date_created': datetime.now().isoformat(),
            'fields': first_line,
            'rows': counter - skipped_rows,
        }

        with open(self._create_new_file_metadata(encoded_file_path), 'w') as f:
            json.dump(metadata, f)

        return hash, size
