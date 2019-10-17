"""Test all DA models"""
# pylint: disable = missing-docstring, no-self-use, too-few-public-methods

import pickle
import unittest.mock
from typing import Generator

import pytest

import digitalarchive.models as models


@pytest.fixture
def mock_unhydrated_documents() -> Generator:
    """Yield a set of dummy records from test fixture."""
    records = pickle.load(
        open(
            "/Users/epikulski/digitalarchive/tests/fixtures/unhydrated_records.pickle",
            "rb",
        )
    )
    yield records


class TestResource:
    @unittest.mock.patch("digitalarchive.models.matching")
    def test_match(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Subject.match(name="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(models.Subject, name="Soviet")

    @unittest.mock.patch("digitalarchive.models.api")
    def test_pull(self, mock_api):
        """Check appropriate endpoint and ID passed to get function."""
        # Prep mock document stub.
        mock_stub_doc = models.Document(
            id="1",
            uri="test_uri",
            title="Test Title",
            description="Test Description",
            doc_date="111111",
            frontend_doc_date="111111",
            slug="test slug",
            source_updated_at="111111",
            source_created_at="111111",
            first_published_at="111111",
        )

        # Prep mock rehydrated document
        mock_hydrated_doc_json = {
            "id": "1",
            "uri": "test_uri",
            "title": "Test Title",
            "description": "Test Description",
            "doc_date": "111111",
            "frontend_doc_date": "111111",
            "slug": "test slug",
            "source_updated_at": "111111",
            "source_created_at": "111111",
            "first_published_at": "111111",
            "source": "Test Source",
        }

        mock_api.DigitalArchive.get.return_value = mock_hydrated_doc_json

        # Pull the doc
        mock_stub_doc.pull()

        # Confirm doc is now hydrated
        assert mock_stub_doc.source == "Test Source"


class TestCollection:
    @unittest.mock.patch("digitalarchive.models.matching")
    def test_match(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Collection.match(name="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(
            models.Collection, name="Soviet", model="Collection"
        )


class TestDocument:
    @unittest.mock.patch("digitalarchive.models.matching")
    def test_match(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Document.match(name="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(
            models.Document, name="Soviet", model="Record"
        )
