"""
digitalarchive.models

The module provides documented models and an ORM for interacting with the DA API.
"""
from __future__ import annotations

# Standard Library
import dataclasses
import json
import logging
import copy
from datetime import datetime, date
from typing import List, Any, Optional, Union, Dict, ClassVar
from abc import ABC

# 3rd Party Libraries
import pydantic

# Application Modules
from pydantic import validator

import digitalarchive.matching as matching
import digitalarchive.api as api
import digitalarchive.exceptions as exceptions


class Resource(pydantic.BaseModel, ABC):
    """
    Abstract parent for all DigitalArchive objects.

    We add custom hash and eq fields so that hydrated and unhydrated records are equal.
    """

    id: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not self.__class__ == other.__class__:
            return NotImplemented
        else:
            return self.id == other.id


class MatchingMixin:
    """Abstract parent for Resources that can be searched against."""

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """Find a resource using passed keyword arguments.

        Note:
            If called without arguments, returns all records in the DA .
        """

        # Check that we no invalid search terms were passed.
        for key in kwargs:
            if key not in cls.__fields__.keys():
                raise exceptions.InvalidSearchFieldError

        # Prepare the "term" search field.
        # If we've got both a name and a value, join them.
        if kwargs.get("name") and kwargs.get("value"):
            kwargs["term"] = " ".join([kwargs.pop("name"), kwargs.pop("value")])

        # Otherwise, treat the one that exists as the term.
        elif kwargs.get("name"):
            kwargs["term"] = kwargs.pop("name")
        elif kwargs.get("value"):
            kwargs["term"] = kwargs.pop("value")

        return matching.ResourceMatcher(cls, **kwargs)


class HydrateMixin:
    """Mixin for resources that can be individually accessed and hydrated."""

    def pull(self):
        """Update the resource using data from the DA API."""
        data = api.get(endpoint=self.endpoint, resource_id=self.id)
        self.__init__(**data)

    def hydrate(self):
        """
        Populate all unhydrated fields of a resource.
        """
        # Preserve unhydrated fields.
        unhydrated_fields = copy.copy(self.__dict__)

        # Hydrate
        self.pull()
        hydrated_fields = vars(self)

        # Merge fields
        for key, value in unhydrated_fields.items():
            if (
                hydrated_fields.get(key) is None
                and unhydrated_fields.get(key) is not None
            ):
                hydrated_fields[key] = value

        # Re-initialize the object.
        self.__init__(**hydrated_fields)


class Subject(Resource, MatchingMixin, HydrateMixin):
    """
    A historical topic to which documents can be related.

    Attributes:
        id (str): The ID of the record.
        name (str): The name of the subject.
        value (str): An alias for :attr:`~digitalarchive.models.Subject.name`.
        uri (str): The URI for the Subject in the API.
    """

    name: str

    # Optional fields
    value: Optional[str] = None
    uri: Optional[str] = None

    # Private fields
    endpoint: ClassVar[str] = "subject"


class Language(Resource):
    """
    The original language of a resource.

    Attributes:
        id (str): An ISO 639-2/B language code.
        name (str): The ISO language name for the language.
    """

    name: Optional[str] = None


class Asset(Resource, ABC, HydrateMixin):
    """
    Abstract parent for Translations, Transcriptions, and MediaFiles.

    Note:
        We don't define raw, html, or pdf here because they are not present on
        the stub version of Assets.
    """

    # pylint: disable=too-many-instance-attributes

    filename: str
    content_type: str
    extension: str
    asset_id: str
    source_created_at: str
    source_updated_at: str

    url: Optional[str] = None
    raw: Optional[str] = None
    pdf: Optional[str] = None
    html: Optional[str] = None

    def hydrate(self):
        """Populate all unhydrated fields of a :class:`digitalarchive.models._Asset`."""
        response = api.SESSION.get(
            f"https://digitalarchive.wilsoncenter.org/{self.url}"
        )

        if response.status_code == 200:
            # Preserve the raw content from the DA in any case.
            self.raw = response.content

            # Add add helper attributes for the common filetypes.
            if self.extension == "html":
                self.html = response.text
                self.pdf = None
            elif self.extension == "pdf":
                self.pdf = response.content
                self.html = None
            else:
                logging.warning(
                    "[!] Unknown file format '%s' encountered!", self.extension
                )

        else:
            raise exceptions.APIServerError(
                f"[!] Hydrating asset ID#: %s failed with code: %s",
                self.id,
                response.status_code,
            )


class Transcript(Asset):
    """A transcript of a document in its original language.

    Attributes:
          id (str): The ID# of the Transcript.
          url (str): A URL to accessing the hydrated Transcript.
          html (str): The html of of the Transcript.
          pdf (bytes): A bytes object of the Transcript pdf content.
          raw (str or bytes): The raw content recieved from the DA API for the Transcript.
          filename (str): The filename of the Transcript on the content server.
          content_type (str): The MIME type of the Transcript file.
          extension (str): The file extension of the Transcript.
          asset_id (str): The Transcript's unique ID on the content server.
          source_created_at (str): ISO 8601 timestamp of the first time the Translation was published.
          source_updated_at (str): ISO 8601 timestamp of the last time the Translation was modified.
    """

    url: str
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    raw: Union[str, bytes, None] = None


class Translation(Asset):
    """
    A translation of a Document into a another language.

    Attributes:
        id (str): The ID# of the Translation.
        language (:class:`digitalarchive.models.Language`) The langauge of the Translation.
        html (str): The HTML-formatted text of the Translation.
        pdf (bytes): A bytes object of the Translation pdf content.
        raw (str or bytes): The raw content recieved from the DA API for the Translation.
        filename (str): The filename of the Translation on the content server.
        content_type (str): The MIME type of the Translation file.
        extension (str): The file extension of the Translation.
        asset_id (str): The Translation's unique ID on the content server.
        source_created_at (str): ISO 8601 timestamp of the first time the Translation was published.
        source_updated_at (str): ISO 8601 timestamp of the last time the Translation was modified.
    """

    url: str
    language: Union[Language, dict]
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    raw: Optional[str] = None


class MediaFile(Asset):
    """
    An original scan of a Document.

    Attributes:
        id (str): The ID# of the MediaFile.
        pdf (bytes): A bytes object of the MediaFile content.
        raw (str or bytes): The raw content received from the DA API for the MediaFile.
        filename (str): The filename of the MediaFile on the content server.
        content_type (str): The MIME type of the MediaFile file.
        extension (str): The file extension of the MediaFile.
        asset_id (str): The MediaFile's unique ID on the content server.
        source_created_at (str): ISO 8601 timestamp of the first time the MediaFile was published.
        source_updated_at (str): ISO 8601 timestamp of the last time the MediaFile was modified.
    """

    path: str

    def __init__(self, **data):
        data["url"] = data.get("path")
        super().__init__(**data)


class Contributor(Resource, MatchingMixin, HydrateMixin):
    """
    An individual person or organization that contributed to the creation of the document.

    Contributors are typically the Document's author, but for meeting minutes and similar documents,
    a Contributor may simply be somebody who was in attendance at the meeting.

    Attributes:
        id (str): The ID# of the Contributor.
        name (str): The name of the contributor.
        uri (str): The URI of the contributor metadata on the DA API.
    """

    name: str
    value: Optional[str] = None
    uri: Optional[str] = None
    endpoint: ClassVar[str] = "contributor"


class Donor(Resource):
    """
    An entity whose resources helped publish or translate a document.

    Attributes:
        id (str): The ID# of the Donor.
        name (str): The name of the Donor.
    """

    name: str
    endpoint: ClassVar[str] = "donor"


class Coverage(Resource, MatchingMixin, HydrateMixin):
    """
    A geographical area referenced by a Document.

    Attributes:
        id (str): The ID# of the geographic Coverage.
        name (str): The name of geographic coverage area.
        value (str): An alias to :attr:`~digitalarchive.models.Coverage.name`.
        uri (str): URI to the Coverage's metadata on the DA API.
        parent (:class:`~digitalarchive.models.Coverage`): The parent coverage,
            if any
        children: (list of :class:`~digitalarchive.models.Covereage`):
            Subordinate geographical areas, if any.
    """

    name: str
    uri: str
    value: Optional[str] = None
    parent: Union[Coverage, List, None] = None  # Inconsistent endpoint. Parent is either a dict or a empty list.
    children: Optional[List[Coverage]] = None
    endpoint: ClassVar[str] = "coverage"

    @validator("parent")
    def _process_parent(cls, parent):
        if isinstance(parent, list):
            return None
        return parent


Coverage.update_forward_refs()


class Collection(Resource, MatchingMixin, HydrateMixin):
    """
    A collection of Documents on a single topic

    Attributes:
        name (str): The title of the collection.
        slug (str): A url-friendly name of the collection.
        uri (str): The URI of the record on the DA API.
        parent(:class:`digitalarchive.models.Collection`): A `Collection` containing the `Collection`.
        model (str): A sting name of the model used to differentiate `Collection` and `Document` searches in the DA API.
        value (str): A string identical to the `title` field.
        description (str): A 1-2 sentence description of the `Collection`'s content.
        short_description (str): A short description that appears in search views.
        main_src (str): Placeholder
        no_of_documents (str):  The count of documents contained in the collection.
        is_inactive (str): Whether the collection is displayed in the collections list.
        source_created_at(:class:`datetime.datetime`): Timestamp of when the Document was first added to the DA.
        source_updated_at(:class:`datetime.datetime`): Timestamp of when the Document was last edited.
        first_published_at(:class:`datetime.datetime`): Timestamp of when the document was first made publically
            accessible.
    """

    # pylint: disable=too-many-instance-attributes
    # Required Fields
    name: str
    slug: str

    # Optional Fields
    uri: Optional[str] = None
    parent: Optional[Collection] = None
    model: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    main_src: Optional[str] = None
    thumb_src: Optional[str] = None
    no_of_documents: Optional[str] = None
    is_inactive: Optional[str] = None
    source_created_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    first_published_at: Optional[datetime] = None

    # Internal Fields
    endpoint: ClassVar[str] = "collection"


Collection.update_forward_refs()


class Repository(Resource, MatchingMixin, HydrateMixin):
    """
    The archive or library possessing the original, physical Document.

    Attributes:
        id (str): The ID# of the Repository.
        name (str): The name of the repository
        uri (str): The URI for the Repository's metadata on the Digital Archive API.
        value (str): An alias to :attr:`~digitalarchive.models.Repository.name`
    """

    name: str
    uri: Optional[str] = None
    value: Optional[str] = None
    endpoint: ClassVar[str] = "repository"


class Publisher(Resource):
    """
    An organization involved in the publication of the document.

    Attributes:
        id (str): The ID# of the Publisher.
        name (str): The name of the Publisher.
    """

    name: str
    value: str
    endpoint: ClassVar[str] = "publisher"


class Type(Resource):
    """
    The type of a document (memo, report, etc).

    Attributes:
        id (str): The ID# of the Type.
        name (str): The name of the resource Type.
    """

    name: str


class Right(Resource):
    """
    A copyright notice attached to the Document.

    Attributes:
        id (str): The ID# of the Copyright type.
        name (str): The name of the Copyright type.
        rights (str): A description of the copyright requirements.
    """

    name: str
    rights: str


class Classification(Resource):
    """
    A classification marking applied to the original Document.

    Attributes:
        id (str): The ID# of the Classification type.
        name (str): A description of the Classification type.
    """

    name: str


class Document(Resource, MatchingMixin, HydrateMixin):
    """
    A Document corresponding to a single record page on digitalarchive.wilsoncenter.org.

    Note:
        Avoid constructing Documents directly--use the `match` function to create
        Documents by keyword search or by ID.


    **Attributes present on all Documents:**

    Attributes:
        id (str): The ID# of the record in the DA.
        title (str): The title of a document.
        description (str): A one-sentence description of the document's content.
        doc_date (str): The date of the document's creation in ``YYYYMMDD`` format.
        frontend_doc_date (str): How the date appears when presented on the DA website.
        slug (str): A url-friendly name for the document. Not currently used.
        source_created_at(:class:`datetime.datetime`): Timestamp of when the Document was first added to the DA.
        source_updated_at(:class:`datetime.datetime`): Timestamp of when the Document was last edited.
        first_published_at(:class:`datetime.datetime`): Timestamp of when the document was first made publically
            accessible.

    **Attributes present only on hydrated Documents**

    These attributes are aliases of :class:`UnhydratedField` until :func:`Document.hydrate` is called on the Document.

    Attributes:
        source (str): The archive where the document was retrieved from.
        type (:class:`digitalarchive.models.Type`): The type of the document (meeting minutes, report, etc.)
        rights (:obj:`list` of :class:`digitalarchive.models.Right`): A list of entities holding the copyright of the
            Document.
        pdf_generated_at (str): The date that the  combined source, translations, and transcriptions PDF. was generated.
        date_range_start (:class:`datetime.date`): A rounded-down date used to standardize approximate dates for
            date-range matching.
        sort_string_by_coverage (str): An alphanumeric identifier used by the API to sort search results.
        main_src (str): The original Source that a Document was retrieved from.
        model (str): The model of a record, used to differentiate collections and keywords in searches.
        donors (:obj:`list` of :class:`digitalarchive.models.Donor`): A list of donors whose funding make the acquisiton
            or translation of a document possible.
        subjects (:obj:`list` of :class:`digitalarchive.models.Subject`): A list of subjects that the document is tagged
            with.
        transcripts (:obj:`list` of :class:`digitalarchive.models.Transcript`): A list of transcripts of the document's
            contents.
        translations (:obj:`list` of :class:`digitalarchive.models.Translation`): A list of translations of the original
            document.
        media_files (:obj:`list` of :class:`digitalarchive.models.MediaFile`): A list of attached original scans of the
            document.
        languages(:obj:`list` of  :class:`digitalarchive.models.Language`): A list of langauges contained in the
            document.
        creators (:obj:`list` of :class:`digitalarhive.models.Creator`): A list of persons who authored the document.
        original_coverages (:obj:`list` of :class:`digitalarchive.models.Coverage`): A list of geographic locations
            referenced in the document.
        collections (:obj:`list` of :class:`digitalarchive.models.Collection`): A list of Collections that contain this
            document.
        attachments (:obj:`list` of :class:`digitalarchive.models.Document`): A list of Documents that were attached to
            the Document.
        links (:obj:`list` of :class:`digitalarchive.models.Document`): A list of topically related documents.
        respositories (:obj:`list` of :class:`digitalarchive.models.Repository`): A list of archives/libraries
            containing this document.
        publishers (:obj:`list` of :class:`digitalarchive.models.Publisher`): A list of Publishers that released the
            document.
        classifications (:obj:`list` of :class:`digitalarchive.models.Publisher`): A list of security classification
            markings present on the document.
    """

    # pylint: disable=too-many-instance-attributes

    # Required Fields
    uri: str
    title: str
    doc_date: str
    frontend_doc_date: str
    slug: str
    source_created_at: datetime
    source_updated_at: datetime
    first_published_at: datetime

    # Optional Fields
    description: Optional[str] = None
    source: Optional[str] = None
    type: Optional[List[Type]] = None
    rights: Optional[Right] = None
    pdf_generated_at: Optional[datetime] = None
    date_range_start: Optional[date] = None
    sort_string_by_coverage: Optional[str] = None
    main_src: Optional[
        Any
    ] = None  # TODO: Never seen one of these in the while, so not sure how to handle.
    model: Optional[str] = None

    # Optional Lists:

    donors: Optional[List[Donor]] = None
    subjects: Optional[List[Subject]] = None
    transcripts: Optional[List[Transcript]] = None
    translations: Optional[List[Translation]] = None
    media_files: Optional[List[MediaFile]] = None
    languages: Optional[List[Language]] = None
    contributors: Optional[List[Contributor]] = None
    creators: Optional[List[Contributor]] = None
    original_coverages: Optional[List[Coverage]] = None
    collections: Optional[List[Collection]] = None
    attachments: Optional[List[Any]] = None  # TODO: Should be "document" -- fix.
    links: Optional[List[Any]] = None
    repositories: Optional[List[Repository]] = None
    publishers: Optional[List[Publisher]] = None
    classifications: Optional[List[Classification]] = None

    # Private properties
    endpoint: ClassVar[str] = "record"

    @validator("date_range_start", pre=True)
    def _parse_date_range_start(cls, doc_date) -> date:
        """Transform a DA-style date string to a Python datetime."""
        if isinstance(doc_date, date):
            return doc_date
        elif doc_date is None:
            return doc_date

        # Try to parse it as a normal one
        try:
            return date.fromisoformat(doc_date)
        except ValueError:
            pass

        year = int(doc_date[:4])
        month = int(doc_date[4:6])
        day = int(doc_date[-2:])
        return date(year, month, day)

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """
        Search for a Document by keyword, or fetch one by ID.

        Matching on the Document model runs a full-text search using keywords passed via the  title and description
        keywords. Results can also be limited by dates or by related records, as described below.

        Note:
            Title and description keywords are not searched for individually. All
            non-date or child record searches are concatenated to single querystring.

        Note:
            Collection and other related record searches use `INNER JOIN` logic when
            passed multiple related resources.

        **Allowed search fields:**

        Args:
            title (:obj:`str`, optional): Title search keywords.
            description (:obj:`str`, optional): Title search keywords.
            start_date (:class:`datetime.date`, optional): Return only Documents with a `doc_date` after the passed
                `start_date`.
            end_date (:class:`datetime.date`, optional): Return only Documents with a `doc_date` before the passed
                `end_date`.
            collections (:obj:`list` of :class:`digitalarchive.models.Collection`, optional): Restrict results to
                Documents contained in all of the passed Collections.
            publishers (:obj:`list` of :class:`digitalarchive.models.Publisher`, optional): Restrict results to
                Documents published by all of the passed Publishers.
            repositories (:obj:`list` of :class:`digitalarchive.models.Repository`, optional) Restrict results to
                Documents contained in all of the passed Repositories.
            coverages (:obj:`list` of :class:`digitalarchive.models.Coverage`, optional) Restrict results to Documents
                relating to all of the passed geographical Coverages.
            subjects (:obj:`list` of :class:`digitalarchive.models.Subject`) Restrict results to Documents tagged with
                all of the passed subjects
            contributors (:obj:`list of :class:`digitalarchive.models.Contributor`) Restrict results to Documents whose
                authors include all of the passed contributors.
            donors (list(:class:`digitalarchive.models.Donor`)) Restrict results to Documents who were obtained or
                translated with support from all of the passed donors.
            languages (:class:`digitalarchive.models.Language` or str) Restrict results to Documents by language of
                original document. If passing a string, you must pass an ISO 639-2/B language code.
            translation (:class:`digitalarchive.models.Translation`) Restrict results to Documents for which there
                is a translation available in the passed Language.
            theme (:class:`digitalarchive.models.Theme`) Restrict results to Documents belonging to the passed Theme.

        Returns:
            An instance of (:class:`digitalarchive.matching.ResourceMatcher`) containing any records responsive to the
                search.
        """
        # Limit search to only Documents (this excludes Collections from search result).
        kwargs["model"] = "Record"

        # Check that search keywords are valid.
        allowed_search_fields = [
            *cls.__fields__.keys(),
            "start_date",
            "end_date",
            "themes",
            "model",
        ]
        for key in kwargs:
            if key not in allowed_search_fields:
                logging.error(
                    f"[!] {key} is not a valid search term for {cls}. Valid terms: {allowed_search_fields}"
                )
                raise exceptions.InvalidSearchFieldError

        # Process date searches if they are present.
        if any(key in kwargs.keys() for key in ["start_date", "end_date"]):
            kwargs = Document._process_date_searches(kwargs)

        # Process language searches if they are present.
        if "languages" in kwargs.keys():
            kwargs = Document._process_language_search(kwargs)

        # Process any related model searches.
        if any(
            key in kwargs.keys()
            for key in [
                "collections",
                "publishers",
                "repositories",
                "original_coverages",
                "subjects",
                "contributors",
                "donors",
                "languages",
                "translations",
                "themes",
            ]
        ):
            kwargs = Document._process_related_model_searches(kwargs)

        # Prepare the 'q' fulltext search field.
        keywords = []
        for field in ["name", "title", "description", "slug", "q"]:
            if kwargs.get(field) is not None:
                keywords.append(kwargs.pop(field))
        kwargs["q"] = " ".join(keywords)

        # Reformat fields that accept lists. This makes the queries inner joins rather than union all.
        for field in ["donor", "subject", "contributor", "coverage", "collection"]:
            if field in kwargs.keys():
                kwargs[f"{field}[]"] = kwargs.pop(field)

        # Run the match.
        return matching.ResourceMatcher(cls, **kwargs)

    def hydrate(self, recurse: bool = False):
        """
        Downloads the complete version of the Document with metadata for any related objects.

        Args:
            recurse (bool): If true, also hydrate subordinate and related records records.
        """
        # Preserve unhydrated fields.
        unhydrated_fields = copy.copy(self.__dict__)

        # Hydrate
        self.pull()
        hydrated_fields = vars(self)

        # Merge fields
        for key, value in unhydrated_fields.items():
            if (
                hydrated_fields.get(key) is None
                and unhydrated_fields.get(key) is not None
            ):
                hydrated_fields[key] = value

        # Re-initialize the object.
        self.__init__(**hydrated_fields)

        # Hydrate Assets
        if recurse is True:
            [transcript.hydrate() for transcript in self.transcripts]
            [translation.hydrate() for translation in self.translations]
            [media_file.hydrate() for media_file in self.media_files]
            [collection.hydrate() for collection in self.collections]

    @staticmethod
    def _process_date_searches(query: dict) -> dict:
        """Run formatting and type checks against  date search fields."""
        date_search_terms = ["start_date", "end_date"]

        # Handle open-ended date searches.
        if "start_date" in query.keys() and "end_date" not in query.keys():
            query["end_date"] = date.today()
        elif "end_date" in query.keys() and "start_date" not in query.keys():
            # Pull earliest record date from API.
            da_date_range = api.get_date_range()
            start_date = Document._parse_date_range_start(da_date_range["begin"])
            query["start_date"] = start_date

        # Transform datetime objects into formatted string and return
        for field in date_search_terms:
            search_date = query[field]
            if isinstance(search_date, date):
                query[
                    field
                ] = f"{search_date.year}{search_date.strftime('%m')}{search_date.strftime('%d')}"

            # If passed a string but its wrong length, raise.
            elif isinstance(search_date, str) and len(search_date) != 8:
                logging.error("[!] Invalid date string! Format is: YYYYMMDD")
                raise exceptions.MalformedDateSearch

        return query

    @staticmethod
    def _process_related_model_searches(query: dict) -> dict:
        """
        Process and format searches by related models.

        We have to re-name the fields from plural to singular to match the DA format.
        """
        multi_terms = {
            "collections": "collection",
            "publishers": "publisher",
            "repositories": "repository",
            "original_coverages": "coverage",
            "subjects": "subject",
            "contributors": "contributor",
            "donors": "donor",
            "languages": "language",
            "translations": "translation",
            "themes": "theme",
        }

        # Rename each term to singular
        for key, value in multi_terms.items():
            if key in query.keys():
                query[value] = query.pop(key)

        # Build list of terms we need to parse
        terms_to_parse = []
        for term in multi_terms.values():
            if term in query.keys():
                terms_to_parse.append(term)

        # transform each term list into a list of IDs
        for term in terms_to_parse:
            query[term] = [str(item.id) for item in query[term]]

        # Special handling for langauges, translations, themes.
        # Unlike they above, they only accept singular values
        for term in ["language", "translation", "theme"]:
            if term in query.keys():
                if len(query[term]) > 1:
                    logging.error(f"[!] Cannot filter for more than one %s", term)
                    raise exceptions.InvalidSearchFieldError
                # Pull out the singleton.
                query[term] = query[term][0]

        # Return the reformatted query.
        return query

    @staticmethod
    def _process_language_search(query: dict) -> dict:
        """
        Process a language search

        Looks up the DA's language ID# for user provided ISO 639-2/B language codes and updates the query.

        Args:
            query (dict): A ResourceMatcher query.

        Returns:
            dict: A query dict with a ISO 639-2/B string replaced with appropriate Language object.
        """
        parsed_languages = []
        for language in query["languages"]:
            # Check if ID# is instance of language, bail on yes.
            if isinstance(language, Language):
                parsed_languages.append(language)

            # If str, lookup ID# of language
            elif isinstance(language, str) and len(language) == 3:
                parsed_languages.append(Language(id=language))

            else:
                raise exceptions.MalformedLanguageSearch

            # Replace kwarg with Langauge object.
            query["languages"] = parsed_languages
            return query


class Theme(Resource, HydrateMixin):
    """
    A parent container for collections on a single geopolitical topic.

    Note:
        Themes never appear on any record model, but can be passed as a search param to Document.

    Attributes:
        id (str): The ID# of the Theme.
        slug (str): A url-friendly version of the theme title.
        title (str): The name of the Theme.
        description (str): A short description of the Theme contents.
        main_src: A URI for the Theme's banner image on the Digital Archive website.
        has_map (str): A boolean value for whether the Theme has an accompanying map on the Digital Archive website.
        has_timeline(str) : A boolean value for whether the Theme has a Timeline on the Digital Archive website.
        featured_collections (list of :class:`~digitalarchive.models.Collection`): A list of related collections.
        dates_with_events (list): A list of date ranges that the Theme has timeline entries for.
    """

    # Required fields
    slug: str

    # Optional Fields
    title: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    main_src: Optional[str] = None
    uri: Optional[str] = None
    featured_resources: Optional[List[dict]] = None
    has_map: Optional[str] = None
    has_timeline: Optional[str] = None
    featured_collections: Optional[List[Collection]] = None
    dates_with_events: Optional[list] = None

    # Private fields.
    endpoint: ClassVar[str] = "theme"

    def pull(self):
        """
        Downloads the complete Theme object from the DA and re-initializes the dataclass..

        Note: The Theme pull method differs from from the pull methods of other models as Themes use the `slug`
        attribute as a primary key, rather than the `id` attribute.
        """
        data = api.get(endpoint=self.endpoint, resource_id=self.slug)
        self.__init__(**data)
