"""Unit Tests of matching digitalarchive.matching."""
# pylint: disable=missing-function-docstring, no-self-use,too-few-public-methods

# Standard Library
import unittest.mock

# 3rd Party Libraries
import pytest

# Application models
import digitalarchive.exceptions as exceptions
import digitalarchive.models as models
import digitalarchive.matching as matching


class TestResourceMatcher:
    """Test digitalarchive.matching.ResourceMatcher."""

    @unittest.mock.patch("digitalarchive.api.search")
    def test_match_by_keyword_single_page(self, mock_search):
        # Set up mock response.
        mock_search.return_value = {
            "metadata": {"matches_estimated": 1},
            "list": [unittest.mock.MagicMock()],
        }
        matching.ResourceMatcher(models.Publisher, name="test_name")
        mock_search.assert_called_with(
            model=models.Publisher.endpoint,
            params={"name": "test_name", "itemsPerPage": 200},
        )

    @unittest.mock.patch(
        "digitalarchive.matching.ResourceMatcher._get_all_search_results"
    )
    @unittest.mock.patch("digitalarchive.api.search")
    def test_match_by_keyword_multi_page(self, mock_search, mock_get_all):
        # Set up mock response.
        mock_search.return_value = {
            "metadata": {"matches_estimated": 2},
            "list": [unittest.mock.MagicMock(), unittest.mock.MagicMock()],
        }

        # Run Search.
        matching.ResourceMatcher(models.Publisher, items_per_page=1, name="test_name")

        # Verify generator function called.
        mock_get_all.assert_called_with(mock_search())

    @unittest.mock.patch("digitalarchive.matching.ResourceMatcher._record_by_id")
    def test_match_by_id(self, mock_get_by_id):
        """Test Search API called with proper params."""
        # Run match
        matching.ResourceMatcher(models.Resource, id=1)

        # Check search called with proper params.
        mock_get_by_id.assert_called_once()

    def test_invalid_keyword(self):
        with pytest.raises(exceptions.InvalidSearchFieldError):
            models.Resource.match(test="test")
