import logging
import requests
import base64
import json

from edmtool import errors
from tqdm import tqdm
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from urllib.parse import urlparse, urlunparse

TIMEOUT = 300


class UploaderClient:

    def __init__(self, base_url, r_token):
        if base_url is not None:
            self._set_base_url(base_url)

        self.headers = {}
        self.auth_token = None
        self.token = r_token

    def _set_base_url(self, base_url):
        parsed_url = urlparse(base_url)
        if parsed_url.scheme != 'https':
            raise errors.BaseUrlIsNotHTTPS(f"Base Url {base_url} is not HTTPS. Please change it.")
        path = parsed_url.path.rstrip('/')
        self.base_url = urlunparse(parsed_url._replace(path=path))

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
                raise e
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
                                     timeout=TIMEOUT,
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
                                      timeout=TIMEOUT,
                                      headers=self.headers)
            return self._handle_response(response)
        except requests.Timeout:
            logging.error(f"The request to update the db with the ID {id} and timed out.")
            return None

    def _upload_database(self, db_id, encoded_file_path, encoded_file_size):
        with open(encoded_file_path, 'rb') as f, tqdm(
                total=encoded_file_size,
                unit='B',
                unit_scale=True,
                desc=f"INFO: Uploading encoded EDM DB file into the database \"{db_id}\"",
                initial=0) as pbar:

            def file_reader(file_obj, chunk_size=1024):
                while True:
                    chunk = file_obj.read(chunk_size)
                    if not chunk:
                        break
                    pbar.update(len(chunk))
                    yield chunk

            headers = {"Content-Type": "application/octet-stream"}
            headers.update(self.headers)

            try:
                response = requests.post(f"{self.base_url}/api/v2/edm/cli/db/upload/{db_id}",
                                         headers=headers,
                                         data=file_reader(f),
                                         timeout=TIMEOUT)
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
        return self._upload_database(db_id, encoded_file_path, metadata["size"])

    def get_token(self):
        if self.auth_token:
            return
        authz_url: str = f"{self.base_url}/user-management/auth/token"
        token_contents = base64.b64decode(self.token).decode("utf-8")
        try:
            response = requests.post(authz_url,
                                     data=token_contents,
                                     headers={'content-type': 'application/json'},
                                     timeout=TIMEOUT)
            self.auth_token = self._handle_response(response)
            self.headers = {"Authorization": f"Bearer {self.auth_token}"}

        except requests.Timeout:
            logging.error(f"The request get the token in the API timed out.")
            return None
