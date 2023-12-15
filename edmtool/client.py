import logging
import requests
import base64
import json

from tqdm import tqdm
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


class UploaderClient:

    def __init__(self, base_url, r_token):
        self.base_url = base_url
        self.headers = {}
        self.token = r_token

    def _handle_response(self, response):
        try:
            response.raise_for_status()

            if 'application/json' in response.headers.get('content-type', ''):
                return response.json()
            else:
                return response.text
        except requests.HTTPError as e:
            try:
                error_response = response.json()
                raise Exception(
                    f"Server status: {response.status_code}, response: {error_response}.\n")
            except json.JSONDecodeError:
                return e
        except Exception as e:
            raise Exception(f"An error occurred: {e}\n")

    def create_database(self, name, description, size, algorithm, checksum, fields, rows):
        self.get_token()

        payload = {
            "name": name,
            "description": description,
            "size": size,
            "rows": rows,
            "algorithm": algorithm,
            "checksum": checksum,
            "fields": fields,
        }

        try:
            response = requests.post(f"{self.base_url}/api/v1/edm/cli/db",
                                     json=payload,
                                     timeout=100,
                                     headers=self.headers)
            return self._handle_response(response)
        except requests.Timeout:
            logging.error(f"The request to create the db with the name {name} and timed out.")
            return None

    def update_database(self, id: str, size, algorithm, checksum, fields, rows):
        self.get_token()

        payload = {
            "size": size,
            "rows": rows,
            "algorithm": algorithm,
            "checksum": checksum,
            "fields": fields,
        }

        try:
            response = requests.patch(f"{self.base_url}/api/v1/edm/cli/db/{id}",
                                      json=payload,
                                      timeout=100,
                                      headers=self.headers)
            return self._handle_response(response)
        except requests.Timeout:
            logging.error(f"The request to update the db with the ID {id} and timed out.")
            return None

    def _upload_database(self, db_id, encoded_file_path, encoded_file_size, encoded_file_name):
        upload_size = encoded_file_size

        with tqdm(total=upload_size,
                  unit='B',
                  unit_scale=True,
                  desc=f"Uploading encoded EDM DB file into the database \"{db_id}\"",
                  initial=0) as pbar:
            with open(encoded_file_path, 'rb') as open_file:
                fields = {"id": db_id, "file": (encoded_file_name, open_file)}

                e = MultipartEncoder(fields=fields)
                m = MultipartEncoderMonitor(
                    e, lambda monitor: pbar.update(monitor.bytes_read - pbar.n))
                headers = {"Content-Type": m.content_type}
                headers.update(self.headers)

                try:
                    response = requests.post(self.base_url + "/api/v1/edm/cli/db/upload",
                                             headers=headers,
                                             data=m)
                    return self._handle_response(response)
                except requests.Timeout:
                    pbar.close()
                    logging.error(
                        f"The request to upload the db {db_id} located at {encoded_file_path} timed out."
                    )
                    return None
                except Exception as e:
                    pbar.close()
                    logging.error(f"An error occurred: {e}\n")
                    return None

    def upload(self, db_id, encoded_file_path, metadata):
        self.get_token()
        return self._upload_database(db_id, encoded_file_path, metadata["size"],
                                     metadata["filename"])

    def get_token(self):
        authz_url: str = f"{self.base_url}/user-management/auth/token"
        token_contents = base64.b64decode(self.token).decode("utf-8")
        try:
            response = requests.post(authz_url,
                                     data=token_contents,
                                     headers={'content-type': 'application/json'},
                                     timeout=10)
            self.headers = {"Authorization": f"Bearer {self._handle_response(response)}"}
        except requests.Timeout:
            logging.error(f"The request get the token in the API timed out.")
            return None
