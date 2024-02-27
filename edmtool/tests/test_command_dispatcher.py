import unittest
from unittest.mock import patch, Mock
from edmtool.command_dispatcher import CommandDispatcher


class TestCommandDispatcher(unittest.TestCase):

    @patch('edmtool.command_dispatcher.CommandHandler')
    @patch('argparse.ArgumentParser.parse_args')
    def test_capture_create(self, mock_parse_args, mock_CommandHandler):
        mock_args = Mock()
        mock_args.action = "create"
        mock_args.base_url = "https://localhost:8080"
        mock_args.token = "test_token"
        mock_parse_args.return_value = mock_args

        dispatcher = CommandDispatcher()
        dispatcher.capture()

        mock_CommandHandler.return_value.create.assert_called_once_with(mock_args)

    @patch('edmtool.command_dispatcher.CommandHandler')
    @patch('argparse.ArgumentParser.parse_args')
    def test_capture_create_and_upload(self, mock_parse_args, mock_CommandHandler):
        mock_args = Mock()
        mock_args.action = "create_and_upload"
        mock_args.base_url = "https://localhost:8080"
        mock_args.token = "test_token"
        mock_parse_args.return_value = mock_args

        dispatcher = CommandDispatcher()
        dispatcher.capture()

        mock_CommandHandler.return_value.create_and_upload.assert_called_once_with(mock_args)

    @patch('edmtool.command_dispatcher.CommandHandler')
    @patch('argparse.ArgumentParser.parse_args')
    def test_capture_upload(self, mock_parse_args, mock_CommandHandler):
        mock_args = Mock()
        mock_args.action = "upload"
        mock_args.base_url = "https://localhost:8080"
        mock_args.token = "test_token"
        mock_parse_args.return_value = mock_args

        dispatcher = CommandDispatcher()
        dispatcher.capture()

        mock_CommandHandler.return_value.upload.assert_called_once_with(mock_args)

    @patch('edmtool.command_dispatcher.CommandHandler')
    @patch('argparse.ArgumentParser.parse_args')
    def test_capture_exception(self, mock_parse_args, mock_CommandHandler):
        mock_args = Mock()
        mock_args.action = "create"
        mock_parse_args.return_value = mock_args
        mock_CommandHandler.return_value.create.side_effect = Exception("Test Exception")

        dispatcher = CommandDispatcher()
        with self.assertLogs() as cm:
            dispatcher.capture()
            self.assertTrue(any("Operation create errored." in log for log in cm.output))


if __name__ == '__main__':
    unittest.main()
