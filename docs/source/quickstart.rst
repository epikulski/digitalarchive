**********
Quickstart
**********

The `Document` is the basic unit of content in the Digital Archive. Every document is accompanied by metadata, including
a short description of its content, information about the archive it was obtained, subjects it is tagged with,
alongside other information.

Most of the Digital Archive's documents originate from outside the United States. Translations are available for most
documents, as well as original scans in some cases. The :class:`digitalarchive.Document` model describes the available
methods and attributes for documents.

The `digitalarchive` package also provides models for other kinds of Digital Archive resources, such as `Subject`,
`Collection`, `Theme`, (geographic) `Coverage`, and `Repository`. These models can be used as filters when searching for
documents. Consult the **API** documentation for a full description of availbe models.

Searching
---------
The `Document`, `Contributor`, `Coverage`, `Collection`, `Subject`, and `Repository`, models each expose a `match()`
method that can be used to search for documents. The method accepts a list of keyword arguments corresponding to the
attributes of the matched for model.

Example:
    >>> import digitalarchive
    >>> docs = digitalarchive.Document.match(description="Cuban Missile Crisis")

The match method always returns an instance of :class:`digitalarchive.matching.ResourceMatcher`.  ResourceMatcher
exposes a `first()` method for to accessing a single document and an `all()` for accessing a list of all respondant
records.

Searching for a record by its ID field always returns a single record and ignores any other keyword arguments.

Example:
    >>> test_search = digitalarchive.Document.match(id="175898")
    >>> test_search.count
    1
    >>> doc = test_search.first()
    >>> doc.title
    'Memorandum on a Discussion held by the Consul-General of the USSR in Ürümchi, G.S. DOBASHIN, with the Secretary of the Party Committee of the Xinjiang Uyghur Autonomous Region, Comrade LÜ JIANREN'


Filtering Searches
------------------

One can limit searches to recordds created between specific dates by passing a `start_date` keyword, an `end_date`
keyword, or both.

    >>> from datetime import date
    >>> digitalarchive.Document.match(start_date=date(1989, 4, 15), end_date=date(1989, 5, 4))
    ResourceMatcher(model=<class 'digitalarchive.models.Document'>, query={'start_date': '19890415', 'end_date': '19890504', 'model': 'Record', 'itemsPerPage': 200, 'q': ''}, count=15)

Searches can also be limited to records contained within a specific collection, subject, or other container. Matches for
Documents can be filtered by one or more `Collection`, `Repository`, `Coverage`, `Subject`, `Contributor`, and `Donor`
instances:

    >>> xinjiang_collection = digitalarchive.Collection.match(id="491").first()
    >>> xinjiang_collection.name
    “Local Nationalism" in Xinjiang, 1957-1958
    >>> docs = digitalarchive.Document.match(collections=[xinjiang_collection])
    >>> docs.count
    9

Hydrating Search Results
------------------------


