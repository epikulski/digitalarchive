[![Build Status](https://travis-ci.com/epikulski/digitalarchive.svg?token=DF1254Zmz3xWHziFRx2x&branch=master)](https://travis-ci.com/epikulski/digitalarchive)
# Digital Archive
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
