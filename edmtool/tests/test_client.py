import unittest

from io import BytesIO
from unittest.mock import patch, Mock, mock_open
from edmtool.client import UploaderClient


class TestUploaderClient(unittest.TestCase):

    def setUp(self):
        self.client = UploaderClient(base_url="http://test.com",
                                     r_token="dXNlcm5hbWU6cGFzc3dvcmQ=")  # username:password

    @patch('requests.post')
    @patch('requests.post')
    def test_create_database(self, mock_post_token, mock_post_create):
        db_id = "7ac4d7c8-a255-47fd-9713-9a018f6bc223"
        db_name = "test_name"
        db_desc = "test_desc"
        algo = "spooky"
        upload_link = "/v1/edm/cli/db/upload"
        checksum = "abcdefgh"

        mock_post_create_response = Mock()
        mock_post_create_response.status_code = 201
        mock_post_create_response.json.return_value = {
            "success": True,
            "db_name": db_name,
            "id": db_id,
            "upload_link": upload_link
        }
        mock_post_create_response.headers = {"content-type": "application/json; charset=utf-8"}
        mock_post_create_response.raise_for_status.return_value = None
        mock_post_create.return_value = mock_post_create_response

        mock_post_token = Mock()
        mock_post_token.status_code = 200
        mock_post_token.json.return_value = "TOKEN_VALUE"
        mock_post_token.headers = {"content-type": "html/text; charset=utf-8"}
        mock_post_token.raise_for_status.return_value = None
        mock_post_token.return_value = mock_post_token

        response = self.client.create_database(db_name, db_desc, 1, 100, 5000, algo, checksum)
        self.assertTrue(response["success"])

    @patch("builtins.open", new_callable=mock_open, read_data=b"mocked file content")
    @patch('requests.post')
    @patch('requests.post')
    def test_upload(self, mock_post_token, mock_post_upload, mock_open_file):
        db_id = "test_db_id"
        test_file_path = "/home/test_file_path.csv"

        mock_open_file.return_value = BytesIO(b"mocked file content")

        mock_post_token = Mock()
        mock_post_token.status_code = 200
        mock_post_token.json.return_value = "TOKEN_VALUE"
        mock_post_token.headers = {"content-type": "html/text; charset=utf-8"}
        mock_post_token.raise_for_status.return_value = None
        mock_post_token.return_value = mock_post_token

        mock_metadata = {"filename": "test_filename.csv", "size": 15000, "checksum": "abc"}
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.text = "success"
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.headers = {"Content-Length": 15000}
        mock_post_upload.return_value = mock_post_response

        response = self.client.upload(db_id, test_file_path, mock_metadata)
        self.assertEqual(response, 'success')


if __name__ == '__main__':
    unittest.main()
