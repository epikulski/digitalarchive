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

        # Check that there are data in the results:
        for record in records:
            assert record.description is not None

    def test_match_by_keyword_multipage(self):
        """Check that we can handle multi-page searches."""
        results = digitalarchive.Document.match(description="afghanistan")
        records = list(results.all())

        # Check we got all the promised records
        assert len(records) == results.count

        # Check that record types are as expected.
        for record in records:
            assert isinstance(record, digitalarchive.Document)

    def test_hydrate(self):
        # Fetch and hydrate a single record.
        results = digitalarchive.Document.match(description="soviet eurasia")
        records = list(results.all())
        record = records[0]

        # Check that fields start unhydrated.
        assert record.translations is digitalarchive.models.UnhydratedField
        assert record.transcripts is digitalarchive.models.UnhydratedField
        record.hydrate()

        # Check that expected fields were hydrated.
        assert len(record.translations) != 0
        assert len(record.transcripts) != 0

        for field in record.__dataclass_fields__.keys():
            assert (
                record.__getattribute__(field)
                is not digitalarchive.models.UnhydratedField
            )

        for translation in record.translations:
            assert isinstance(translation, digitalarchive.models.Translation)

        for transcript in record.transcripts:
            assert isinstance(transcript, digitalarchive.models.Transcript)

    def test_hydrate_resultset(self):
        results = digitalarchive.Document.match(description="soviet eurasia")
        results.hydrate()
        results = results.all()

    def test_date_range(self):
        results = digitalarchive.Document.match(start_date="19500101", end_date="19500101")
        records = list(results.all())
        self.fail()

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
        assert record.first_published_at is digitalarchive.models.UnhydratedField
        assert record.source_created_at is digitalarchive.models.UnhydratedField

        # Hydrate the record
        record.hydrate()

        # Check that fields are now populated.
        assert record.first_published_at is not digitalarchive.models.UnhydratedField
        assert record.source_created_at is not digitalarchive.models.UnhydratedField

    def test_hydrate_resultset(self):
        results = digitalarchive.Collection.match(description="europe")
        results.hydrate()
        results = list(results.all())

        # Check all results are correct type.
        for result in results:
            assert isinstance(result, digitalarchive.Collection)

        # Check that docs are hydrated.
        for result in results:
            assert result.uri is not digitalarchive.models.UnhydratedField
            assert result.no_of_documents is not digitalarchive.models.UnhydratedField
            assert result.description is not digitalarchive.models.UnhydratedField


class TestTranslation:
    def test_hydrate(self):
        """Test hydration method for digitalarchive.models._Asset"""
        # Fetch a translation
        test_doc = digitalarchive.Document.match(id=208400).first()
        test_translation = test_doc.translations[0]

        # Check expected fields are unhydrated
        assert test_translation.html is digitalarchive.models.UnhydratedField
        assert test_translation.raw is digitalarchive.models.UnhydratedField

        # Hydrate the translation.
        test_translation.hydrate()

        # Confirm html fields are now present.
        assert test_translation.html is not digitalarchive.models.UnhydratedField
        assert test_translation.raw is not digitalarchive.models.UnhydratedField


class TestSubject:
    def test_match_by_keyword(self):
        results = digitalarchive.Subject.match(name="soviet")
        records = list(results.all())

        # Check we got all the promised records
        assert len(records) == results.count

        # Check they were properly parsed.
        for record in records:
            assert isinstance(record, digitalarchive.Subject)

    def test_match_by_id(self):
        results = digitalarchive.Subject.match(id="1311")
        record = results.first()

        # Check type
        assert isinstance(record, digitalarchive.Subject)

        # Check some fields for expected values.
        assert record.name == "Iraq--Foreign relations--Soviet Union"
        assert record.uri == "/srv/subject/1311.json"

    def test_hydrate(self):
        # Fetch a document
        test_doc = digitalarchive.Document.match(id=208400).first()
        test_subject = test_doc.subjects[0]

        # Check record is unhydrated
        assert test_subject.uri is digitalarchive.models.UnhydratedField
        assert test_subject.value is digitalarchive.models.UnhydratedField

        # Hydrate the record
        test_subject.hydrate()

        # Check new fields are there.
        for field in test_subject.__dataclass_fields__:
            assert (
                test_subject.__getattribute__(field)
                is not digitalarchive.models.UnhydratedField
            )

    def test_hydrate_resultset(self):
        results = digitalarchive.Subject.match(name="Burma")
        results.hydrate()
        results = list(results.all())

        # Check all results are correct type.
        for result in results:
            assert isinstance(result, digitalarchive.Subject)

        # Check new fields are there.
        for result in results:
            for field in result.__dataclass_fields__:
                assert (
                    result.__getattribute__(field)
                    is not digitalarchive.models.UnhydratedField
                )


class TestRepository:
    def test_match_by_id(self):
        # Fetch a known record.
        results = digitalarchive.Repository.match(id="5")
        repo = results.first()

        # Check type
        assert isinstance(repo, digitalarchive.models.Repository)

        # Check some fields.
        assert (
            repo.name == "Conflict Records Research Center, National Defense University"
        )
        assert repo.uri == "/srv/repository/5.json"
        assert (
            repo.value
            == "Conflict Records Research Center, National Defense University"
        )

    def test_match_by_keyword(self):
        # Search for some records.
        results = digitalarchive.Repository.match(name="Russian")
        repos = list(results.all())

        # Inspect results
        assert len(repos) == results.count

        for repo in repos:
            assert isinstance(repo, digitalarchive.models.Repository)


class TestContributor:
    def test_match_by_id(self):
        # Fetch a known record.
        results = digitalarchive.Contributor.match(id="5")
        contributor = results.first()

        # Check type
        assert isinstance(contributor, digitalarchive.models.Contributor)

        # Check some fields.
        assert contributor.name[:9] == "Agostinho"
        assert contributor.value[:9] == "Agostinho"
        assert contributor.uri == "/srv/contributor/5.json"

    def test_match_by_keyword(self):
        # Search for some records.
        results = digitalarchive.Contributor.match(name="John")
        repos = list(results.all())

        # Inspect results
        assert len(repos) == results.count

        for repo in repos:
            assert isinstance(repo, digitalarchive.models.Contributor)

    def test_hydrate(self):
        # Get a document & contributor
        test_doc = digitalarchive.Document.match(id=177540).first()
        test_contributor = test_doc.contributors[0]

        # make sure they start blank
        assert test_contributor.uri is digitalarchive.models.UnhydratedField
        assert test_contributor.value is digitalarchive.models.UnhydratedField

        # Hydrate the model
        test_contributor.hydrate()

        # Check new fields are there.
        for field in test_contributor.__dataclass_fields__:
            assert (
                test_contributor.__getattribute__(field)
                is not digitalarchive.models.UnhydratedField
            )


class TestCoverage:
    def test_match_by_id(self):
        coverage = digitalarchive.Coverage.match(id="295").first()

        # Check for some expected fields.
        assert isinstance(coverage, digitalarchive.Coverage)
        assert coverage.parent is None
        assert len(coverage.children) != 0
        assert coverage.name == "Central Africa"
        assert coverage.value == "Central Africa"
        assert coverage.uri == "/srv/coverage/295.json"

    def test_match_by_keyword(self):
        results = digitalarchive.Coverage.match(name="Africa")
        coverages = list(results.all())

        # Inspect results.
        assert results.count == len(coverages)
        for coverage in coverages:
            assert isinstance(coverage, digitalarchive.Coverage)

    def test_hydrate(self):
        results = digitalarchive.Coverage.match(name="Africa")
        coverage = results.first()

        # Confirm fields start dehydrated
        assert coverage.children is digitalarchive.models.UnhydratedField
        assert coverage.parent is digitalarchive.models.UnhydratedField

        # Hydrate the field
        coverage.hydrate()

        # Check fields are now hydrated
        assert coverage.children is not digitalarchive.models.UnhydratedField
        assert coverage.parent is not digitalarchive.models.UnhydratedField

        for coverage in coverage.children:
            assert isinstance(coverage, digitalarchive.Coverage)

    def test_hydrate_resultset(self):
        results = digitalarchive.Coverage.match(name="Africa")
        results.hydrate()
        coverage = list(results.all())

        # Check that there are no unhydrated fields in the resultant records.
        for coverage in coverage:
            assert coverage.parent is not digitalarchive.models.UnhydratedField
            assert coverage.children is not digitalarchive.models.UnhydratedField
