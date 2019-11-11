********
Cookbook
********
Examples of common operations encountered using the Digital Archive client.

Search for a resource by keyword
--------------------------------
Run a keyword search across the title, description, and document content.
    >>> from digitalarchive import Document
    >>> # Find a document
    >>> results = Document.match(description="Cuban Missile Crisis")
    >>> # Check the number of results from the search:
    >>> results.count
    656
    >>> # Acccess a single record.
    >>> document = results.first()

Filter a search by a related record
-----------------------------------
Search for a collection and then find documents contanied in that collection:
    >>> from digitalarchive import Document, Collection
    >>> # Find an interesting collection:
    >>> xinjiang_collection = Collection.match(name="xinjiang").first()
    >>> # Find records contained in that colletion:
    >>> documents = Document.match(collections=[xinjiang_collection]).all()

Filter a Document search by language
------------------------------------
Limit a search to documents in a certain language:
    >>> from digitalarchive.models import Document, Language
    >>> RYaN_docs = Document.match(description="project ryan", languages=[Language(id="ger")])
    >>> RYaN_docs.count
    32

Filter a Document search by date
--------------------------------
Search for records after a certain date:
    >>> from digitalarchive import Document
    >>> from datetime import date
    >>> postwar_docs = Document.match(start_date=date(1945, 9, 2))
    >>> postwar_docs.count
    13088

Search for records before a certain date:
    >>> from digitalarchive import Document
    >>> from datetime import date
    >>> prewar_docs = Document.match(end_date=date(1945, 9, 2))
    >>> prewar_docs.count
    269

Search for docs between two dates:
    >>> from digitalarchive import Document
    >>> from datetime import date
    >>> coldwar_docs = Document.match(start_date=date(1945, 9, 2), end_date=date(1991, 12, 26))
    >>> coldwar_docs.count
    12792

Download the complete metadata for a document
---------------------------------------------
    >>> from digitalarchive import Document
    >>> chernobyl_doc = Document.match(description="pripyat evacuation order").first()
    >>> chernobyl_doc.repositories
    <class 'digitalarchive.models.UnhydratedField'>
    >>> chernobyl_doc.hydrate()
    >>> chernobyl_doc.repositories
    [Repository(id='84', name='Central State Archive of Public Organizations of Ukraine (TsDAHOU)')]

Download the original scan of a document.
-----------------------------------------
Original scans (referred to internally as :class:`~digitalarchive.models.MediaFile`) are child records of
:class:`~digitalarchive.models.Document`. They must be hydrated before the PDF content can be accessed.

    >>> from digitalarchive import Document
    >>> chernobyl_doc = Document.match(id="208406").first()
    >>> original_scan = chernobyl_doc.media_files[0]
    >>> original_scan.pdf
    <class 'digitalarchive.models.UnhydratedField'>
    >>> original_scan.hydrate()
    >>> type(original_scan.pdf)
    <class 'bytes'>
    >>> len(original_scan.pdf)
    10936093
    >>> with open(original_scan.filename, "wb") as outfile:
    ...     outfile.write(original_scan.pdf)

Download the translation or transcript of a document.
-----------------------------------------------------
Like original scans, :class:`~digitalarchive.models.Transcript` and :class:`~digitalarchive.models.Translation` are
child records of :class:`~digitalarchive.models.Document`. They must also be hydrated before their content can be
accessed. Translations and transcripts are typically presented as HTML files, but may sometimes be presetened as PDFs.

    >>> from digitalarchive import Document
    >>> chernobyl_doc = Document.match(id="208406").first()
    >>> translation = chernobyl_doc.translations[0]
    >>> translation.hydrate()
    >>> translation.filename
    'TranslationFile_208406.html'
    >>> with open(translation.filename, "wb") as outfile:
    ...     outfile.write(translation.html)
