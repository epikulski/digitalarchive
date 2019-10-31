"""Test API interaction code."""
# pylint: disable=no-self-use,invalid-name,missing-docstring

# Standard Library
import unittest.mock

# 3rd Party Libs
import pytest

# Library Modules
import digitalarchive.api
from digitalarchive.models import Subject


class TestSearch:
    """Unit Tests of the digitalarchive.api ORM class."""

    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_search(self, mock_requests):
        mock_requests.get().status_code = 200
        params = {"q": "Soviet China", "model": "Record"}
        results = digitalarchive.api.search(model="record", params=params)
        # Check search terms properly parameterized.
        mock_requests.get.assert_called_with(
            "https://digitalarchive.wilsoncenter.org/srv/record.json",
            params={"q": "Soviet China", "model": "Record"},
        )

        # Check function returns json on success.
        assert results is mock_requests.get().json.return_value

    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_search_empty_params(self, mock_requests):
        mock_requests.get().status_code = 200

        # Send Request
        digitalarchive.api.search(model="record", params={"model": "Record", "q": "test"})

        # Check search terms properly parameterized.
        mock_requests.get.assert_called_with(
            "https://digitalarchive.wilsoncenter.org/srv/record.json",
            params={"q": "test", "model": "Record"},
        )

    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_search_error(self, mock_requests):
        # Set up internal server error mock.
        mock_requests.get().status_code = 500

        with pytest.raises(Exception):
            # Send Request
            digitalarchive.api.search(model="record")


class TestGet:
    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_get(self, mock_requests):
        """Confirm digitalarchive.api sends a correctly formed request."""
        # pylint: disable=redefined-outer-name
        # Set up mock
        mock_requests.get().status_code = 200
        mock_response = unittest.mock.MagicMock()
        mock_requests.get().json.return_value = mock_response

        # Query API for dummy record.
        data = digitalarchive.api.get(endpoint="document", resource_id="1")

        # Confirm url was constructed correctly.
        intended_url = "https://digitalarchive.wilsoncenter.org/srv/document/1.json"
        mock_requests.get.assert_called_with(intended_url)

        # Confirm correct data was returned
        assert data == mock_response

    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_get_fail(self, mock_requests):
        """Confirm digitalarchive.api raises exception on server errors."""
        # Set up mock
        mock_requests.get().status_code = 500

        # Confirm exception raised.
        with pytest.raises(Exception):
            digitalarchive.api.get(endpoint="document", resource_id="1")

class TestGetDateRange:

    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_get_date_range(self, mock_session):
        test_date_range = digitalarchive.api.get_date_range()
        mock_session.get.assert_called_once()
        assert test_date_range is mock_session.get().json()