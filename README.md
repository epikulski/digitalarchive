
# Digital Archive

[![Build Status](https://travis-ci.com/epikulski/digitalarchive.svg?token=DF1254Zmz3xWHziFRx2x&branch=master)](https://travis-ci.com/epikulski/digitalarchive)
[![codecov](https://codecov.io/gh/epikulski/digitalarchive/branch/master/graph/badge.svg?token=UOd5l8vX6b)](https://codecov.io/gh/epikulski/digitalarchive)

A Python 3.7+ interface for the Wilson Center's [Digital Archive](https://digitalarchive.wilsoncenter.org) ("DA") of historical primary sources. This library provides a rough ORM for searching and accessing documents and other resources in the Digital Archive. 

## Usage

```python
# Import the model you are interested in searching against:
from digitalarchive.models import Document 

# Get a set of all matching documents:
soviet_documents = Document.match(name="soviet").all()

# Grab a single, specific document:
test_doc = Document.match(id="112566").first()

# Pull transcripts, translations, and original scans of documents:
test_doc.pull()
test_html = test_doc.transcripts[0].html

# Pull the transcripts, translations, and original scans of an entire resultset:
test_doc_list = Document.match(name="soviet")
test_doc_list.hydrate()

# Or just download the stubs for every Document in the DA and do as you please:
all_documents = Document.match()
```

## Disclaimers
* This is an unofficial library. I am not affiliated with the Wilson Center in any way. It is my understanding that the API is unlikely to change in the near future, but I cannot guarantee that this library won't break without warning. 
* If you plan to scrape the DA, please be respectful. 

## Planned Features
* Support for searching by date range. 
* Asynchronous hydration of large result sets.
* Support searches for collections that include keyword hits from the collections `short_description` field by changing changing collection searches from the `collection.json` to `record.json` endpoint.  

## Known bugs in the DigitalArchive API.
These are known bugs in the DA's API that I have observed while developing this library. I've worked around them where possible.
* The `Collection` model has inconsistent fields between searching via the record.json endpoint and the collection.json endpoint.

