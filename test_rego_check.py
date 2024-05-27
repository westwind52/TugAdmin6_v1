
# Generated by CodiumAI

from Folder.myroutes.aircraft import rego_check

# Dependencies:
# pip install pytest-mock
import pytest

class TestRegoCheck:

    #  Returns True if registration is present in database
    def test_returns_true_if_registration_present(self, mocker):
        mocker.patch('Folder.myroutes.aircraft.Aircraft.query.filter_by')
        mock_check = mocker.MagicMock()
        mock_check.one_or_none.return_value = True
        Folder.myroutes.aircraft.Aircraft.query.filter_by.return_value = mock_check

        result = rego_check('GXM')

        assert result is True

    #  Returns False if registration is not present in database
    def test_returns_false_if_registration_not_present(self, mocker):
        mocker.patch('Folder.myroutes.aircraft.Aircraft.query.filter_by')
        mock_check = mocker.MagicMock()
        mock_check.one_or_none.return_value = None
        Folder.myroutes.aircraft.Aircraft.query.filter_by.return_value = mock_check

        result = rego_check('GXM')

        assert result is False

    #  Accepts a string as input
    def test_accepts_string_input(self, mocker):
        mocker.patch('Folder.myroutes.aircraft.Aircraft.query.filter_by')
        mock_check = mocker.MagicMock()
        mock_check.one_or_none.return_value = None
        Folder.myroutes.aircraft.Aircraft.query.filter_by.return_value = mock_check

        result = rego_check('GXM')

        assert result is False

    #  Returns False if input is not a string
    def test_returns_false_if_input_not_string(self, mocker):
        mocker.patch('Folder.myroutes.aircraft.Aircraft.query.filter_by')
        mock_check = mocker.MagicMock()
        mock_check.one_or_none.return_value = None
        Folder.myroutes.aircraft.Aircraft.query.filter_by.return_value = mock_check

        result = rego_check(123)

        assert result is False

    #  Returns False if input is an empty string
    def test_returns_false_if_input_empty_string(self, mocker):
        mocker.patch('Folder.myroutes.aircraft.Aircraft.query.filter_by')
        mock_check = mocker.MagicMock()
        mock_check.one_or_none.return_value = None
        Folder.myroutes.aircraft.Aircraft.query.filter_by.return_value = mock_check

        result = rego_check('')

        assert result is False

    #  Returns False if input is None
    def test_returns_false_if_input_none(self, mocker):
        mocker.patch('Folder.myroutes.aircraft.Aircraft.query.filter_by')
        mock_check = mocker.MagicMock()
        mock_check.one_or_none.return_value = None
        Folder.myroutes.aircraft.Aircraft.query.filter_by.return_value = mock_check

        result = rego_check(None)

        assert result is False