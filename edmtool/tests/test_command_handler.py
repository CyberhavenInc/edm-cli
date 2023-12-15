import argparse
import unittest

from unittest.mock import Mock, patch
from edmtool.command_handler import CommandHandler
from edmtool.errors import MissingArgumentsError


class TestCommandHandler(unittest.TestCase):

    @patch('edmtool.utils.Read_metadata_file')
    @patch('edmtool.utils.Validate_create_args')
    @patch('edmtool.utils.Get_file_size')
    @patch('edmtool.utils.Print_user_friendly_response')
    def test_create(self, mock_print, mock_get_file_size, mock_validate_args,
                    mock_read_metadata_file):
        mock_client = Mock()
        mock_client.create_database.return_value = {"success": True}
        mock_get_file_size.return_value = 1000
        mock_validate_args.return_value = []
        mock_read_metadata_file.return_value = {
            "filename": "base_file.csv",
            "size": 1500,
            "checksum": "abcdeg",
            "algo": "spooky",
            "seed": 123456,
            "fields": ["FirstName", "Last Name", "Employee ID"],
            "rows": 8
        }

        args = argparse.Namespace(action="create",
                                  name="test_db",
                                  description="test_description",
                                  version=1,
                                  proximity=100,
                                  metadata_file_path="test_path")

        handler = CommandHandler(mock_client)
        response = handler.create(args)

        self.assertTrue(response["success"])

    @patch('edmtool.utils.Get_file_size')
    @patch('edmtool.utils.Calculate_file_sha256_checksum')
    @patch('edmtool.utils.Read_metadata_file')
    @patch('edmtool.utils.Print_user_friendly_response')
    def test_upload(self, _, mock_read_metadata_file, mock_checksum, mock_file_size):
        mock_client = Mock()
        mock_client.upload.return_value = "success"

        mock_read_metadata_file.return_value = {
            "filename": "test_filename.csv",
            "size": 15000,
            "checksum": "abcde",
            "fields": ["FirstName", "Last Name", "Employee ID"],
            "rows": 8
        }
        mock_checksum.return_value = "abcde"
        mock_file_size.return_value = 15000

        args = argparse.Namespace(action="upload",
                                  id="1234",
                                  metadata_file_path="/path/test_path.csv")

        handler = CommandHandler(mock_client)
        response = handler.upload(args)

        self.assertTrue(response)

    @patch('edmtool.utils.Calculate_file_sha256_checksum')
    @patch('edmtool.utils.Read_metadata_file')
    @patch('edmtool.utils.Get_file_size')
    @patch('edmtool.utils.Print_user_friendly_response')
    def test_create_and_upload(self, _, mock_get_file_size, mock_read_metadata_file, mock_checksum):
        mock_get_file_size.return_value = 1000
        mock_checksum.return_value = "abcdefg"

        mock_read_metadata_file.return_value = {
            "filename": "base_file.csv",
            "size": 1000,
            "checksum": "abcdefg",
            "algo": "spooky",
            "seed": 123456,
            "fields": ["FirstName", "Last Name", "Employee ID"],
            "rows": 8
        }

        mock_client = Mock()
        mock_client.create_database.return_value = {"success": True, "id": "1234"}
        mock_client.upload.return_value = "success"

        args = argparse.Namespace(action="create_and_upload",
                                  name="test_db",
                                  description="test_description",
                                  version=1,
                                  proximity=100,
                                  metadata_file_path="test_path")

        handler = CommandHandler(mock_client)
        handler.create_and_upload(args)

        mock_client.create_database.assert_called_once()
        mock_client.upload.assert_called_once()

    @patch('edmtool.utils.Read_metadata_file')
    @patch('edmtool.utils.Get_file_size')
    @patch('edmtool.utils.Print_user_friendly_response')
    def test_missing_args(self, _, mock_get_file_size, mock_read_metadata_file):
        mock_client = Mock()
        mock_read_metadata_file.return_value = {"filename": "base_file.csv"}

        args = argparse.Namespace(action="upload",
                                  id=None,
                                  metadata_file_path="/home/test_path.csv")

        handler = CommandHandler(mock_client)
        with self.assertRaises(MissingArgumentsError):
            handler.upload(args)


if __name__ == '__main__':
    unittest.main()
