"""Test all DA models"""
# pylint: disable = missing-docstring, no-self-use, too-few-public-methods

import unittest.mock
from datetime import date, datetime

import pytest

import digitalarchive.models as models
import digitalarchive.exceptions as exceptions


@unittest.mock.patch("digitalarchive.models.matching")
class TestMatchableResource:
    def test_match_name(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Subject.match(name="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(models.Subject, term="Soviet")

    def test_match_value(self, mock_matching):
        models.Subject.match(value="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(models.Subject, term="Soviet")

    def test_match_handle_term_and_name(self, mock_matching):
        models.Subject.match(name="Soviet", value="China")
        mock_matching.ResourceMatcher.assert_called_with(
            models.Subject, term="Soviet China"
        )


class TestHydrateableResource:
    @unittest.mock.patch("digitalarchive.models.api")
    def test_pull(self, mock_api):
        """Check appropriate endpoint and ID passed to get function."""
        # Prep mock document stub.
        mock_stub_doc = models.Document(
            id="1",
            uri="test_uri",
            title="Test Title",
            description="Test Description",
            doc_date="20100910",
            frontend_doc_date="2019-10-26 16:12:00",
            slug="test slug",
            source_updated_at="2019-10-26 16:12:00",
            source_created_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
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
            "source_updated_at": "2019-10-26 16:12:00",
            "source_created_at": "2019-10-26 16:12:00",
            "first_published_at": "2019-10-26 16:12:00",
            "source": "Test Source",
            "subjects": [],
            "transcripts": [],
            "media_files": [],
            "languages": [],
            "creators": [],
            "collections": [],
            "attachments": [],
            "links": [],
            "translations": [],
            "contributors": [],
            "original_coverages": [],
            "repositories": [],
            "classifications": [],
        }

        mock_api.get.return_value = mock_hydrated_doc_json

        # Pull the doc
        mock_stub_doc.pull()

        # Confirm doc is now hydrated
        assert mock_stub_doc.source == "Test Source"

    @unittest.mock.patch("digitalarchive.models.api.get")
    def test_hydrate(self, mock_api):
        """Test the zipping logic during hydration.

        We use a subject instance here for convenience.
        """

        # Prep mocks
        subject = models.Subject(id="1", name="test_name", value="test_value")
        mock_api.return_value = {"id": "1", "name": "test_name", "uri": "test_uri"}

        # Hydrate the resource.
        subject.hydrate()

        # Check that mock pull was called.
        mock_api.assert_called_once()

        # check that result is merged
        assert subject.name == "test_name"
        assert subject.value == "test_value"
        assert subject.uri == "test_uri"

class TestCollection:
    @unittest.mock.patch("digitalarchive.models.matching")
    def test_match(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Collection.match(name="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(
            models.Collection, term="Soviet"
        )

    def test_datetime_parsing(self):
        # Create a mock collection.
        collection = models.Collection(
            id=1,
            name="test",
            slug="test",
            source_created_at="2019-10-26 15:43:11",
            source_updated_at="2019-10-26 15:43:11",
            first_published_at="2019-10-26 15:43:11",
        )

        # Check that datetimes were properly generated.
        assert isinstance(collection.source_updated_at, datetime)
        assert isinstance(collection.source_created_at, datetime)
        assert isinstance(collection.first_published_at, datetime)

        # Check that datetimes are accurate.
        expected_date = datetime(2019, 10, 26, 15, 43, 11)
        for field in [
            collection.source_created_at,
            collection.source_updated_at,
            collection.first_published_at,
        ]:
            assert field == expected_date


class TestDocument:
    @unittest.mock.patch("digitalarchive.models.matching")
    def test_match(self, mock_matching):
        """Check appropriate model and kwargs passed to matching."""
        models.Document.match(title="Soviet")
        mock_matching.ResourceMatcher.assert_called_with(
            models.Document, q="Soviet", model="Record"
        )

    @unittest.mock.patch("digitalarchive.models.api")
    def test_process_date_search_only_end_date(self, mock_api):
        test_date = date(1989, 4, 15)
        mock_api.get_date_range.return_value = {"begin": "19890414"}
        test_formatted_query = models.Document._process_date_searches({"end_date": test_date})

        # Check that query is properly formed.
        assert test_formatted_query == {"end_date": "19890415", "start_date": "19890414"}

    def test_valid_eq(self):
        """Compare a search result doc and a hydrated doc."""
        hydrated_doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
        )
        unhydrated_doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
            pdf_generated_at="test_pdf_date",
        )

        assert hydrated_doc == unhydrated_doc

    def test_invalid_eq(self):
        doc1 = models.Document(
            id="1",
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
        )
        doc2 = models.Document(
            id="2",
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
        )
        assert doc1 != doc2

    def test_invalid_eq_class(self):
        collection = models.Subject(id="1", name="test_collection")
        contributor = models.Contributor(id="1", name="test_contributor")
        assert collection != contributor

    def test_hash(self):
        # Create dummy records.
        contributor_1 = models.Contributor(id="1", name="test")
        contributor_2 = models.Contributor(id="2", name="test")
        contributor_3 = models.Contributor(id="3", name="test")
        contributor_1_dupe = models.Contributor(id="1", name="test2")

        # Create two overlapping sets.
        contributor_set_1 = set([contributor_1, contributor_2])
        contributor_set_2 = set([contributor_1_dupe, contributor_3])

        # Merge sets
        merged = contributor_set_1 | contributor_set_2

        # Confirm merged sets has no dupes.
        assert merged == {contributor_1, contributor_2, contributor_3}

    def test_date_parsing(self):
        """Check that Document.date_range_start is properly parsed."""
        """Compare a search result doc and a hydrated doc."""
        doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
            date_range_start="20191026",
        )

        assert doc.date_range_start == date(2019, 10, 26)

    @unittest.mock.patch("digitalarchive.models.Document.pull")
    def test_hydrate(self, mock_pull):
        doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
            date_range_start="20191026",
        )

        doc.hydrate()

        # Check that record was pulled
        mock_pull.assert_called_once()

    @unittest.mock.patch("digitalarchive.models.Document.pull")
    def test_hydrate_recursive(self, mock_pull):
        """Check that recursion logic fires when parameter is enabled."""
        mock_transcript = unittest.mock.MagicMock()
        mock_translation = unittest.mock.MagicMock()
        mock_media_file = unittest.mock.MagicMock()
        mock_collection = unittest.mock.MagicMock()
        doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
            date_range_start="20191026",
            transcripts=[mock_transcript],
            translations=[mock_translation],
            media_files=[mock_media_file],
            collections=[mock_collection],
        )
        doc.hydrate(recurse=True)

        # check that mock subordinate records were called.
        mock_transcript.hydrate.assert_called_once()
        mock_translation.hydrate.assert_called_once()
        mock_media_file.hydrate.assert_called_once()
        mock_collection.hydrate.assert_called_once()

    def test_parse_child_records(self):
        test_subject = {
            "id": "1",
            "name": "test_subject"
        }
        doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
            date_range_start="20191026",
            subjects=[test_subject]
            )

        # Check that child records expanded
        assert isinstance(doc.subjects[0], models.Subject)
        assert doc.subjects[0].id == "1"
        assert doc.subjects[0].name == "test_subject"

    def test_parse_child_records_empty(self):
        """Test that empty list fields are handled properly. """
        doc = models.Document(
            id=1,
            uri="test",
            title="test",
            description="test",
            doc_date="test",
            frontend_doc_date="test",
            slug="test",
            source_created_at="2019-10-26 16:12:00",
            source_updated_at="2019-10-26 16:12:00",
            first_published_at="2019-10-26 16:12:00",
            date_range_start="20191026",
            subjects=[]
            )

        # Check that our subject field wasn't modified.
        assert isinstance(doc.subjects, list)

        # check that the other child records are still unhydrated.
        assert doc.publishers is models.UnhydratedField


    def test_process_related_model_searches_languages(self):
        test_language = models.Language(id="1")
        query = {
            "languages": [test_language]
        }

        query = models.Document._process_related_model_searches(query)

        # Check that the ID was pulled out, languages renamed to language.
        assert query["language"] == "1"

    def test_match_invalid_field(self):
        with pytest.raises(exceptions.InvalidSearchFieldError):
            models.Document.match(bad_key="bad_value")

    def test_process_date_search_invalid_date_str(self):
        with pytest.raises(exceptions.MalformedDateSearch):
            models.Document._process_date_searches({"start_date": "YYYYMM"})

    def test_process_date_search_invalid_date_obj(self):
        with pytest.raises(exceptions.MalformedDateSearch):
            models.Document._process_date_searches(
                {"start_date": models.UnhydratedField}
            )

    def test_process_related_model_searches_too_many_params(self):
        with pytest.raises(exceptions.InvalidSearchFieldError):
            models.Document._process_related_model_searches(
                {"languages": [unittest.mock.MagicMock(), unittest.mock.MagicMock()]}
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
        assert test_asset.url is models.UnhydratedField
        assert test_asset.raw is models.UnhydratedField
        assert test_asset.pdf is models.UnhydratedField
        assert test_asset.html is models.UnhydratedField


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
        assert mock_transcript.html is models.UnhydratedField
        assert mock_transcript.pdf is models.UnhydratedField

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
