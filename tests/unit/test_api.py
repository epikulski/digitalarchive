"""Test API interaction code."""
# pylint: disable=no-self-use,invalid-name,missing-docstring

# Standard Library
import asyncio
import unittest
from unittest.mock import MagicMock

# 3rd Party Libs
import pytest

# Library Modules
import digitalarchive.api
import digitalarchive.exceptions as exceptions
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
    @pytest.mark.asyncio
    async def test_get(self):
        """Confirm digitalarchive.api sends a correctly formed request."""
        with unittest.mock.patch("digitalarchive.api.aiohttp.ClientSession") as mock_session:
            mock_response = AsyncContextManagerMock()
            mock_json = MagicMock()
            mock_response.status = 200
            mock_response.json.side_effect = asyncio.coroutine(
                lambda: mock_json
            )
            mock_session().get = MagicMock(
                side_effect=asyncio.coroutine(
                    lambda *args: mock_response
                )
            )

            # Query API for dummy record.
            data = await digitalarchive.api.get(endpoint="document", resource_id="1")

        # Confirm url was constructed correctly.
        intended_url = "https://digitalarchive.wilsoncenter.org/srv/document/1.json"
        mock_session().get.assert_called_with(intended_url)

        # Confirm correct data was returned
        assert data == mock_json

    @pytest.mark.asyncio
    async def test_get_fail(self):
        """Confirm digitalarchive.api raises exception on server errors."""
        with unittest.mock.patch("digitalarchive.api.aiohttp.ClientSession") as mock_session:
            # Set up mock
            mock_response = AsyncContextManagerMock()
            mock_response.status = 500
            mock_session().get = MagicMock(
                side_effect=asyncio.coroutine(
                    lambda *args: mock_response
                )
            )

            # Confirm exception raised.
            test =  asyncio.gather(digitalarchive.api.get(endpoint="document", resource_id="1"), return_exceptions=True)
            await test
            # with pytest.raises(Exception):
            #     response = await digitalarchive.api.get(endpoint="document", resource_id="1")
            self.fail()

class TestGetDateRange:

    @unittest.mock.patch("digitalarchive.api.SESSION")
    def test_get_date_range(self, mock_session):
        test_date_range = digitalarchive.api.get_date_range()
        mock_session.get.assert_called_once()
        assert test_date_range is mock_session.get().json()


class AsyncContextManagerMock(MagicMock):
    """
    A MagicMock compatible with async context managers.

    Note: Python 3.8 has an out-of-the-box awaitable mock, but we include
    this for backwards compatibility to 3.7.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in ('aenter_return', 'aexit_return'):
            setattr(self, key,  kwargs[key] if key in kwargs else MagicMock())

    async def __aenter__(self):
        return self.aenter_return

    async def __aexit__(self, *args):
        return self.aexit_return
