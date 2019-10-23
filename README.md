Digital Archive
===============
[![Build Status](https://travis-ci.com/epikulski/digitalarchive.svg?token=DF1254Zmz3xWHziFRx2x&branch=master)](https://travis-ci.com/epikulski/digitalarchive)
[![codecov](https://codecov.io/gh/epikulski/digitalarchive/branch/master/graph/badge.svg?token=UOd5l8vX6b)](https://codecov.io/gh/epikulski/digitalarchive)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/digitalarchive)

A Python client for the Wilson Center's [Digital Archive](https://digitalarchive.wilsoncenter.org) ("DA") of historical primary sources. This library provides a ORM for searching and accessing documents and other resources in the Digital Archive. 

Usage
-----
```
>>> import digitalarchive

# Search for documents:
>>> soviet_docs = digitalarchive.Document.match(name="soviet").all()

# Collections and other resource types are also searchable.
>> soviet_collections = digitalarchive.Collection.match(name="soviet")

# Grab a single, specific document:
>>> document = digitalarchive.Document.match(id="112566").first()

# Pull transcripts, translations, and original scans of documents:
>>> document.hydrate()
>>> document = test_doc.transcripts[0].html

# Pull the metadata and other assets for an entire resultset.
>>> chernobyl_docs = digitalarchive.Document.match(name="chernobyl")
>>> chernobyl_docs.hydrate()
>>> chernobyl_docs.all()

# Or just download all the documents!
>>> all_documents = digitalarchive.Document.match().all()
```

Disclaimers
-----------
* This is an unofficial library. I am not presently affiliated with the Wilson Center. I understandthat the API is unlikely to change in the near future, but I cannot guarantee that this library won't break without warning. 
* If you plan to scrape the DA, please be respectful. 

Planned Features
----------------
* Support for searching by date range.
* Asynchronous hydration of large result sets.
* For Collections, inlcude keyword hits in `short_description` for searches. (modify collection searches to use the  `record.json` instead of `collection.json` endpoint.

