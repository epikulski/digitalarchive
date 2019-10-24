"""Test retrieving and parsing model from production DA API."""
# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-use, too-few-public-methods

# Application Modules
import digitalarchive


class TestDocument:
    def test_match_by_id(self):
        # Fetch a document
        test_doc = digitalarchive.Document.match(id=208400).first()

        # Check expected values of some fields.
        assert test_doc.title[:38] == "V.V. Shcherbytsky, Head of the Council"
        assert (
            test_doc.description[:52]
            == "Address of the Council of Ministers of Ukrainian SSR"
        )
        assert (
            test_doc.source[:50] == "Archive of the Ukrainian National Chornobyl Museum"
        )

    def test_match_by_keyword(self):
        # Run a small search
        results = digitalarchive.Document.match(description="soviet eurasia")
        records = list(results.all())

        # Check search result isn't empty.
        assert len(records) != 0

        # Check that record types are as expected.
        for record in records:
            assert isinstance(record, digitalarchive.Document)

    def test_match_by_keyword_multipage(self):
        """Check that we can handle multi-page searches."""
        results = digitalarchive.Document.match(description="afghanistan")
        records = list(results.all())

        # Check we got all the promised records
        assert len(records) == results.count

    def test_hydrate(self):
        # Fetch and hydrate a single record.
        results = digitalarchive.Document.match(description="soviet eurasia")
        records = list(results.all())
        record = records[0]
        record.hydrate()

        # Check that expected fields were hydrated.
        assert len(record.translations) != 0
        assert len(record.transcripts) != 0

        for translation in record.translations:
            assert isinstance(translation, digitalarchive.models.Translation)

        for transcript in record.transcripts:
            assert isinstance(transcript, digitalarchive.models.Transcript)

    def test_hydrate_resultset(self):
        results = digitalarchive.Document.match(description="soviet eurasia")
        results.hydrate()
        results = list(results.all())


class TestCollection:
    def test_match_by_keyword(self):
        """Run a collection keyword search and confirm results are as expected."""
        results = digitalarchive.Collection.match(name="soviet")
        records = list(results.all())

        # Check we got all the promised records
        assert len(records) == results.count

        # Check they were properly parsed.
        for record in records:
            assert isinstance(record, digitalarchive.Collection)

    def test_match_by_id(self):
        results = digitalarchive.Collection.match(id="234")
        record = results.first()

        # Check some fields for expected values.
        assert record.name == "China and the Soviet Union in Xinjiang, 1934-1949"
        assert record.slug == "china-and-the-soviet-union-in-xinjiang-1934-1949"

        # Check type
        assert isinstance(record, digitalarchive.Collection)

    def test_hydrate(self):
        results = digitalarchive.Collection.match(name="soviet")
        record = results.first()

        # Check that unhydrated fields are none.
        assert record.first_published_at is None
        assert record.source_created_at is None

        # Hydrate the record
        record.hydrate()

        # Check that fields are now populated.
        assert record.first_published_at is not None
        assert record.source_created_at is not None

    def test_hydrate_resultset(self):
        results = digitalarchive.Collection.match(description="europe")
        results.hydrate()
        results = list(results.all())

        # Check all results are correct type.
        for result in results:
            assert isinstance(result, digitalarchive.Collection)

        # Check that docs are hydrated.
        for result in results:
            assert result.uri is not None
            assert result.no_of_documents is not None
            assert result.description is not None


class TestTranslation:

    def test_hydrate(self):
        """Test hydration method for digitalarchive.models._Asset"""
        # Fetch a translation
        test_doc = digitalarchive.Document.match(id=208400).first()
        test_translation = test_doc.translations[0]

        # Check expected fields are unhydrated
        assert test_translation.html is None
        assert test_translation.raw is None

        # Hydrate the translation.
        test_translation.hydrate()

        # Confirm html fields are now present.
        assert test_translation.html is not None
        assert test_translation.raw is not None
