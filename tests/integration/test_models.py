"""Test retrieving and parsing model from production DA API."""
# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-use, too-few-public-methods

# Standard Library
from datetime import date

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

        for type in record.type:
            assert isinstance(type, digitalarchive.models.Type)

        assert isinstance(record.rights, digitalarchive.models.Right)

    def test_hydrate_recursive(self):
        record: digitalarchive.Document = digitalarchive.Document.match(
            id="121894"
        ).first()
        record.hydrate(recurse=True)

        # Make sure fields of a subordinate record were hydrated.
        for translation in record.translations:
            for key in translation.__dataclass_fields__.keys():
                assert (
                    getattr(translation, key)
                    is not digitalarchive.models.UnhydratedField
                )

    def test_hydrate_resultset(self):
        results = digitalarchive.Document.match(description="soviet eurasia")
        results.hydrate()
        results = results.all()
        assert results.count != 0

        # Check there are no unhydrated fields in the resultant records.
        for result in results:
            for key in result.__dataclass_fields__.keys():
                assert getattr(result, key) is not digitalarchive.models.UnhydratedField

    def test_hydrate_resultset_recursive(self):
        """Hydrate a resultset and confirm child records of results are not dehydrated."""
        results = digitalarchive.Document.match(description="soviet eurasia")
        results.hydrate(recurse=True)
        results = results.all()
        for result in results:
            for translation in result.translations:
                for key in translation.__dataclass_fields__.keys():
                    assert (
                        getattr(translation, key)
                        is not digitalarchive.models.UnhydratedField
                    )

            for transcript in result.transcripts:
                for key in transcript.__dataclass_fields__.keys():
                    assert (
                        getattr(transcript, key)
                        is not digitalarchive.models.UnhydratedField
                    )

    def test_date_range_str(self):
        results = digitalarchive.Document.match(
            start_date="19500101", end_date="19510101"
        )
        records = list(results.all())

        # check records fall within requested dates.
        assert len(records) != 0
        for record in records:
            assert record.date_range_start >= date(1950, 1, 1)
            assert record.date_range_start <= date(1951, 1, 1)

    def test_date_range_obj(self):
        start_date = date(1950, 1, 1)
        end_date = date(1951, 1, 1)
        results = digitalarchive.Document.match(
            start_date=start_date, end_date=end_date
        )
        records = list(results.all())

        # check records fall within requested dates.
        assert len(records) != 0
        for record in records:
            assert record.date_range_start >= date(1950, 1, 1)
            assert record.date_range_start <= date(1951, 1, 1)

    def test_date_range_open_start(self):
        """Test matching when only end_date is provided."""
        end_date = date(1950, 1, 1)
        all_docs = digitalarchive.Document.match(description="armenia")
        date_docs = digitalarchive.Document.match(
            end_date=end_date, description="armenia"
        )

        assert date_docs.count != 0
        assert all_docs.count >= date_docs.count
        for doc in date_docs.all():
            assert doc.date_range_start <= end_date

    def test_date_range_open_end(self):
        """Test matching when only start_date is provided."""
        start_date = date(1950, 1, 1)
        all_docs = digitalarchive.Document.match(description="armenia")
        date_docs = digitalarchive.Document.match(
            description="armenia", start_date=start_date
        )

        assert date_docs.count != 0
        assert all_docs.count >= date_docs.count
        for doc in date_docs.all():
            assert doc.date_range_start >= start_date

    def test_search_by_collection(self):
        """Search for documents within a given collection"""
        collection_1 = digitalarchive.models.Collection(
            id="273", name="Chinese Nuclear Testing", slug="test"
        )
        collection_2 = digitalarchive.models.Collection(
            id="105", name="Chinese Nuclear History", slug="test"
        )
        docs = digitalarchive.Document.match(collections=[collection_1, collection_2])
        docs.hydrate()
        assert docs.count != 0
        for doc in docs.all():
            assert collection_1 in doc.collections and collection_2 in doc.collections

    def test_search_by_publisher(self):
        """Search for documents by a Publisher"""
        publisher = digitalarchive.models.Publisher(id="7", name="happ", value="happ")
        docs = digitalarchive.Document.match(publishers=[publisher])
        docs.hydrate()
        assert docs.count != 0
        for doc in docs.all():
            assert publisher in doc.publishers

    def test_search_by_repository(self):
        """Search for documents by a Repository"""
        repo = digitalarchive.Repository(id="81", name="test")
        docs = digitalarchive.Document.match(repositories=[repo])
        docs.hydrate()
        assert docs.count != 0
        for doc in docs.all():
            assert repo in doc.repositories

    def test_search_by_coverage(self):
        """Search for a document by a Coverage"""
        cov = digitalarchive.Coverage(id="341", name="Abkhazia", uri="test")
        docs = digitalarchive.Document.match(original_coverages=[cov])
        docs.hydrate()
        assert docs.count != 0
        for doc in docs.all():
            assert cov in doc.original_coverages

    def test_search_by_subject(self):
        """Search for a document by Subject"""
        subject = digitalarchive.Subject(
            id="2229", name="China--History--Tiananmen Square Incident, 1989"
        )
        docs = digitalarchive.Document.match(subjects=[subject])
        docs.hydrate()

        assert docs.count != 0
        for doc in docs.all():
            assert subject in doc.subjects

    def test_search_by_contributor(self):
        """Search for a document by Contributor"""
        contributor1 = digitalarchive.models.Contributor(id="636", name="Nixon")
        contributor2 = digitalarchive.models.Contributor(id="1067", name="Zhou Enlai")
        docs = digitalarchive.Document.match(contributors=[contributor1, contributor2])
        docs.hydrate()
        for doc in docs.all():
            assert contributor1 in doc.contributors and contributor2 in doc.contributors

    def test_search_by_donor(self):
        donor1 = digitalarchive.models.Donor(id="12", name="MacArthur")
        donor2 = digitalarchive.models.Donor(id="13", name="Blavatnik")
        docs = digitalarchive.Document.match(donors=[donor1, donor2])

        # Check all docs match at least one of the searched for collections
        for doc in docs.all():
            doc.hydrate()
            assert donor1 in doc.donors and donor2 in doc.donors

    def test_search_by_language(self):
        language = digitalarchive.models.Language(id="mon")
        docs = digitalarchive.Document.match(languages=[language])
        assert docs.count != 0
        docs.hydrate()
        for doc in docs.all():
            assert language in doc.languages

    def test_search_by_language_by_iso_code(self):
        all_docs = digitalarchive.Document.match()
        german_docs = digitalarchive.Document.match(languages=["ger"])
        assert german_docs.count > 0
        assert german_docs.count < all_docs.count

    def test_search_by_translation(self):
        language = digitalarchive.models.Language(id="chi")
        docs = digitalarchive.Document.match(translations=[language])
        docs.hydrate(recurse=True)
        assert docs.count != 0
        for doc in docs.all():
            translation_lang_ids = [
                translation.language.id for translation in doc.translations
            ]
            assert language.id in translation_lang_ids

    def test_search_by_theme(self):
        theme = digitalarchive.models.Theme(id="8", slug="emir-farid-chehab")
        theme_docs = digitalarchive.Document.match(themes=[theme])
        all_docs = digitalarchive.Document.match()
        assert theme_docs.count < all_docs.count


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
        records = results.all()

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

class TestTheme:

    def test_hydrate(self):
        theme = digitalarchive.models.Theme(id="1", slug="cold-war-history")
        theme.hydrate()
        assert theme.title == "Cold War History"
        assert theme.slug == "cold-war-history"

