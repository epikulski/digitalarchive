**********
Quickstart
**********

The `Document` is the basic unit of content in the Digital Archive. Every document is accompanied by metadata that
incudes a short description of its content, information about the archive it was obtained, subjects it is tagged with,
alongside other information. Most of the Digital Archive's holdings originate from non-US archives and are therefore
accompanied by a translation. Original scans are avaialble for some documents.

The `digitalarchive` package also provides models for other kinds of Digital Archive resources, such as `Subject`,
`Collection`, `Theme`, (geographic) `Coverage), and `Repository`. These models can be used to filter searches. Consult
the **API** documentation for a full description of models exposed by the `digitalarchive` package and their attributes.

Searching
---------
The `Document`, `Contributor`, `Coverage`, `Collection`, `Subject`, and `Repository`, models expose a `match()` method
that can be used to find documents. The match model accepts a list of keyword arguments corresponding to the attributes
of the model you are matching against.

    >>> import digitalarchive
    >>> docs = digitalarchive.Document.match(description="Cuban Missile Crisis")

The match method always returns an instance of :class:`digitalarchive.matching.ResourceMatcher`. The ResourceMatcher
class exposes `first()` to access a single document or `all()` to access a list of all documents. It's `count` attribute
can be accessed to check whether there are any respondant resources.


Filtering Searches
------------------


Hydrating Search Results
------------------------


