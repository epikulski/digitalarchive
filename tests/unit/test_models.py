"""Test all DA models"""
# pylint: disable = missing-docstring, no-self-use, too-few-public-methods

import unittest.mock

import pytest

import digitalarchive.models as models


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

        mock_api.get.return_value = mock_hydrated_doc_json

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
            models.Collection, name="Soviet")


class TestDocument:
    @unittest.mock.patch("digitalarchive.models.matching")
    def test_match(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Document.match(name="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(
            models.Document, name="Soviet", model="Record"
        )


class TestAsset:
    def test_init(self):
        """ Test digitalarchive.models_Asset abstract parent can be instantiated."""
        # pylint: disable=protected-access
        # Create an Asset
        test_asset = models._Asset(
            id="testid",
            filename="testfile",
            content_type="test_content_type",
            extension="html",
            asset_id="test_asset_id",
            source_created_at="test_created",
            source_updated_at="test_updated",
        )

        # Make sure url, raw, pdf, html exist but are empty.
        assert test_asset.url is None
        assert test_asset.raw is None
        assert test_asset.pdf is None
        assert test_asset.html is None


class TestTranscript:
    @pytest.fixture
    def mock_transcript(self):
        transcript = models.Transcript(
            id="testid",
            filename="testfile",
            content_type="test_content_type",
            extension="html",
            asset_id="test_asset_id",
            source_created_at="test_created",
            source_updated_at="test_updated",
            url="test_url",
        )
        return transcript

    @unittest.mock.patch("digitalarchive.models.api.SESSION")
    def test_hydrate(self, mock_requests, mock_transcript):
        # Prep mocks.
        mock_requests.get().status_code = 200

        # Run code
        mock_transcript.extension = "html"
        mock_transcript.hydrate()

        # Ensure properly formed URL called
        mock_requests.get.assert_called_with(
            "https://digitalarchive.wilsoncenter.org/test_url"
        )

    @unittest.mock.patch("digitalarchive.models.api.SESSION")
    def test_hydrate_html(self, mock_requests, mock_transcript):
        # Prep mocks.
        mock_requests.get().status_code = 200

        # Run code
        mock_transcript.extension = "html"
        mock_transcript.hydrate()

        # Ensure raw gets set.
        assert mock_transcript.raw is mock_requests.get().content

        # Ensure html gets set
        assert mock_transcript.html is mock_requests.get().text

    @unittest.mock.patch("digitalarchive.models.api.SESSION")
    def test_hydrate_pdf(self, mock_requests, mock_transcript):
        # Prep mocks.
        mock_requests.get().status_code = 200

        # Run code
        mock_transcript.extension = "pdf"
        mock_transcript.hydrate()

        # Ensure raw gets set.
        assert mock_transcript.raw is mock_requests.get().content

        # Ensure html gets set
        assert mock_transcript.pdf is mock_requests.get().content

    @unittest.mock.patch("digitalarchive.models.api.SESSION")
    def test_hydrate_bad_extension(self, mock_requests, mock_transcript):
        # Prep mocks.
        mock_requests.get.return_value.status_code = 200

        # Run code
        mock_transcript.extension = "invalid"
        mock_transcript.hydrate()

        # Make sure we sucessfully made the call without an error.
        mock_requests.get.assert_called()

        # Make sure pdf and html are blank.
        assert mock_transcript.html is None
        assert mock_transcript.pdf is None

    @unittest.mock.patch("digitalarchive.models.api.SESSION")
    def test_hydrate_server_error(self, mock_requests, mock_transcript):
        mock_requests.get().status_code = 500

        with pytest.raises(Exception):
            mock_transcript.hydrate()


class TestTranslation:
    def test_init(self):
        # Instantiate a Translation
        translation = models.Translation(
            id="testid",
            filename="testfile",
            content_type="test_content_type",
            extension="html",
            asset_id="test_asset_id",
            source_created_at="test_created",
            source_updated_at="test_updated",
            url="test_url",
            language={"id": "rus", "name": "Russian"},
        )
        # Confirm that the language field transformed to Language dataclass.
        assert isinstance(translation.language, models.Language)


class TestMediaFile:
    def test_init(self):
        """Check url field is properly set so that hydrate function of parent class will work."""
        media_file = models.MediaFile(
            id="testid",
            filename="testfile",
            content_type="test_content_type",
            extension="html",
            asset_id="test_asset_id",
            source_created_at="test_created",
            source_updated_at="test_updated",
            path="test_path",
        )

        assert media_file.url == "test_path"
