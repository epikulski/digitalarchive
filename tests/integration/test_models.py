"""Test retrieving and parsing model from production DA API."""
# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-use

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
            assert isinstance(translation, digitalarchive.Translation)

        for transcript in record.transcripts:
            assert isinstance(transcript, digitalarchive.Transcript)
