**********
Quickstart
**********

The ``Document`` is the basic unit of content in the Digital Archive. Every document is accompanied by metadata, including
a short description of its content, information about the archive it was obtained, subjects it is tagged with,
alongside other information.

Most of the Digital Archive's documents originate from outside the United States. Translations are available for most
documents, as well as original scans in some cases. The :class:`~digitalarchive.models.Document` model describes the available
methods and attributes for documents.

The ``digitalarchive`` package also provides models for other kinds of resources, such as
:class:`~digitalarchive.models.Subject`, :class:`~digitalarchive.models.Collection`,
:class:`~digitalarchive.models.Theme`, :class:`~digitalarchive.models.Coverage`, and
:class:`~digitalarchive.models.Repository`. These models can be used as filters when searching for
documents. Consult the :doc:`api` documentation for a full description of available models.

Searching
---------
The ``Document``, ``Contributor``, ``Coverage``, ``Collection``, ``Subject``, and ``Repository``, models each expose a
:meth:`~digitalarchive.models.Document.match()` method that can be used to search for documents. The method accepts a
list of keyword arguments corresponding to the attributes of the matched for model.

    >>> from digitalarchive import Document
    >>> docs = Document.match(description="Cuban Missile Crisis")

The match method always returns an instance of :class:`digitalarchive.matching.ResourceMatcher`.  ResourceMatcher
exposes a :meth:`~digitalarchive.matching.ResourceMatcher.first()` method for to accessing a single document and an
:meth:`~digitalarchive.matching.ResourceMatcher.all()` for accessing a list of all respondent records.

    >>> from digitalarchive import Document
    >>> docs = Document.match(description="Cuban Missile Crisis")
    >>> docs.first().title
    "From the Journal of S.M. Kudryavtsev, 'Record of a Conversation with Prime Minister of Cuba Fidel Castro Ruz, 21 January 1961'"

Searching for a record by its ``id`` always returns a single record and ignores any other keyword arguments.

    >>> from digitalarchive import Document
    >>> test_search = Document.match(id="175898")
    >>> test_search.count
    1
    >>> doc = test_search.first()
    >>> doc.title
    'Memorandum on a Discussion held by the Consul-General of the USSR in Ürümchi, G.S. DOBASHIN, with the Secretary of the Party Committee of the Xinjiang Uyghur Autonomous Region, Comrade LÜ JIANREN'


Filtering Searches
------------------
One can limit searches to records created between specific dates by passing a ``start_date`` keyword, an ``end_date``
keyword, or both.

    >>> from digitalarchive import Document
    >>> from datetime import date
    >>> Document.match(start_date=date(1989, 4, 15), end_date=date(1989, 5, 4))
    ResourceMatcher(model=<class 'digitalarchive.models.Document'>, query={'start_date': '19890415', 'end_date': '19890504', 'model': 'Record', 'q': '', 'itemsPerPage': 200}, count=22)

Searches can also be limited to records contained within a specific collection, subject, or other container. Matches for
Documents can be filtered by one or more ``Collection``, ``Repository``, ``Coverage``, ``Subject``, ``Contributor``,
and ``Donor`` instances:

    >>> from digitalarchive import Collection, Document
    >>> xinjiang_collection = Collection.match(id="491").first()
    >>> xinjiang_collection.name
    '“Local Nationalism" in Xinjiang, 1957-1958'
    >>> docs = Document.match(collections=[xinjiang_collection])
    >>> docs.count
    9

Hydrating Search Results
------------------------

Most search results return "unhydrated" instances of resources with incomplete metadata. All attributes that are not yet
available are represented by :class:`NoneType`. Use the
:meth:`~digitalarchive.models.Document.hydrate()` method to download the full metadata for a resource.

    >>> from digitalarchive import Document
    >>> test_doc = Document.match(description="Vietnam War").first()
    >>> test_doc.source is None
    True
    >>> test_doc.hydrate()
    >>> test_doc.source
    'AVPRF f. 0100, op. 34, 1946, p. 253, d. 18. Obtained and translated for CWIHP by Austin Jersild.'

It is also possible to hydrate all of the contents of a search result using the
:meth:`~digitalarchive.matching.ResourceMatcher.hydrate()` method of :class:`~digitalarchive.matching.ResourceMatcher`.
This operation can take some time for large result sets.

    >>> from digitalarchive import Document
    >>> docs = Document.match(description="Taiwan Strait Crisis")
    >>> docs.hydrate()

When hydrating a result set, it it is also possible to recursively hydrate any child records (translations, transcripts,
etc.) in the result set by setting the ``recurse`` parameter of
:meth:`~digitalarchive.matching.ResourceMatcher.hydrate()` to ``True``.

    >>> from digitalarchive import Document
    >>> docs = Document.match(description="Taiwan Strait Crisis")
    >>> docs.hydrate(recurse=True)