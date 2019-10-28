"""Unit Tests of matching digitalarchive.matching."""
# pylint: disable=missing-function-docstring, no-self-use,too-few-public-methods,protected-access,unused-argument

# Standard Library
import unittest.mock
from datetime import date

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
            "pagination": {"totalItems": 1},
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
            "pagination": {"totalItems": 2},
            "list": [unittest.mock.MagicMock(), unittest.mock.MagicMock()],
        }

        # Run Search.
        matching.ResourceMatcher(models.Publisher, items_per_page=1, name="test_name")

        # Verify generator function called.
        mock_get_all.assert_called_with(mock_search())

    @unittest.mock.patch("digitalarchive.matching.ResourceMatcher._record_by_id")
    def test_match_id_field(self, mock_get_by_id):
        """Test Search API called with proper params."""
        # Run match
        mock_get_by_id.return_value = {"list": [{"id": 1}]}
        test_match = matching.ResourceMatcher(models._Resource, id=1)

        # Check search called with proper params.
        mock_get_by_id.assert_called_once()

        # Inspect list for proper data
        match_results = list(test_match.list)
        assert len(match_results) == 1
        assert isinstance(match_results[0], models._Resource)

    @unittest.mock.patch("digitalarchive.api.get")
    def test_match_record_by_id(self, mock_api_get):
        # pylint: disable=protected-access

        # instantiate matcher and reset mock, them run just the method.
        test_matcher = matching.ResourceMatcher(models.Publisher, id=1)
        mock_api_get.reset_mock()

        # Explicitly call record ID method
        test_response = test_matcher._record_by_id()

        # Check api called with correct params.
        mock_api_get.assert_called_with(
            endpoint=models.Publisher.endpoint, resource_id=1
        )

        # check response is correct format
        assert test_response["list"][0] is mock_api_get()

    def test_invalid_keyword(self):
        with pytest.raises(exceptions.InvalidSearchFieldError):
            models._MatchableResource.match(test="test")

    @unittest.mock.patch("digitalarchive.matching.ResourceMatcher._record_by_id")
    def test_first(self, mock_get_by_id):
        # Run match
        mock_get_by_id.return_value = {"list": [{"id": 1}]}
        test_match = matching.ResourceMatcher(models._Resource, id=1).first()

        assert isinstance(test_match, models._Resource)

    @unittest.mock.patch("digitalarchive.api.search")
    def test_all(self, mock_search):
        # Set up mock response.
        mock_search.return_value = {
            "pagination": {"totalItems": 2},
            "list": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}],
        }

        # Run Search.
        results = matching.ResourceMatcher(models.Contributor, items_per_page=10).all()
        results = list(results)

        # Check results are expected type.
        for result in results:
            assert isinstance(result, models.Contributor)

        # Check result list is expected length.
        assert len(results) == 2

    @unittest.mock.patch("digitalarchive.api.search")
    def test_get_all_search_results(self, mock_search):
        # Set up mock response.
        results_page_1 = {
            "pagination": {"page": 1, "totalPages": 2, "totalItems": 2},
            "list": [{"id": 1, "name": "test1", "slug": "testslug"}],
        }

        results_page_2 = {
            "pagination": {"page": 2, "totalPages": 2, "totalItems": 2},
            "list": [{"id": 2, "name": "test2", "slug": "testslug"}],
        }
        mock_search.side_effect = [results_page_1, results_page_1, results_page_2]

        test_matcher = matching.ResourceMatcher(
            models.Collection, items_per_page=1, name="test_name"
        )
        mock_search.reset_mock()
        mock_search.side_effect = [results_page_1, results_page_2]

        # Trigger function under test.
        results = list(test_matcher.list)

        # Check result is as intended
        assert len(results) == 2
        for result in results:
            assert isinstance(result, models.Collection)

    @unittest.mock.patch("digitalarchive.matching.ResourceMatcher._record_by_id")
    def test_repr(self, mock_get_by_id):
        # Run match
        mock_get_by_id.return_value = {"list": [{"id": 1}]}
        test_match = matching.ResourceMatcher(models._Resource, id=1)
        assert (
            str(test_match)
            == "ResourceMatcher(model=<class 'digitalarchive.models._Resource'>, query={'id': 1}, count=1)"
        )

    @unittest.mock.patch("digitalarchive.matching.api")
    def test_process_date_searches_obj(self, mock_api):
        """Create a test object with a date and confirm formatting."""
        test_match = matching.ResourceMatcher(models.Document, id=1)
        test_match.query["start_date"] = date(1950, 1, 1)
        test_match._process_date_searches("start_date")
        assert test_match.query["start_date"] == "19500101"

    @unittest.mock.patch("digitalarchive.matching.api")
    def test_process_date_searches_str(self, mock_api):
        """Pass a unsupported type to date search, confirm error raised """
        test_match = matching.ResourceMatcher(models.Document, id=1)
        test_match.query["start_date"] = "19500101"
        test_match._process_date_searches("start_date")
        assert test_match.query["start_date"] == "19500101"

    @unittest.mock.patch("digitalarchive.matching.api")
    def test_process_date_search_invalid_model(self, mock_api):
        test_match = matching.ResourceMatcher(models.Subject, id=1)
        test_match.query["start_date"] = "19500101"
        with pytest.raises(exceptions.InvalidSearchFieldError):
            test_match._process_date_searches("start_date")

    @unittest.mock.patch("digitalarchive.matching.api")
    def test_process_date_searches_invalid_len(self, mock_api):
        test_match = matching.ResourceMatcher(models.Document, id=1)
        test_match.query["start_date"] = "195001"
        with pytest.raises(exceptions.MalformedDateSearch):
            test_match._process_date_searches("start_date")

    @unittest.mock.patch("digitalarchive.matching.api")
    def test_process_date_searches_invalid_type(self, mock_api):
        """Pass a unsupported type to date search, confirm """
        test_match = matching.ResourceMatcher(models.Document, id=1)
        test_match.query["start_date"] = 1.1
        with pytest.raises(exceptions.MalformedDateSearch):
            test_match._process_date_searches("start_date")
