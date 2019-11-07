.. DigitalArchive documentation master file, created by
   sphinx-quickstart on Fri Nov  1 15:21:18 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The unofficial client for the Wilson Center Digital Archive
===========================================================

The **digitalrchive** Python library is a client and ORM for accessing, searching, and downloading
historical documents and their accompanying scans, translations, and transcriptions from the
`Wilson Center's Digital Archive`_ of historical primary sources.

Features
--------
* Search for documents and other Digital Archive resources by keyword.
* Easily retrieve translations, transcriptions, and related records of any document.
* Fully documented models for all of the Digital Archive resource types.

Installation
------------
To install the latest stable version of **digitalarchive**, simply use pip_::

    $ python3 -m pip install digitalarchive

Usage
-----

    >>> import digitalarchive
    >>> digitalarchive.Subject.match(name="Tiananmen Square Incident").first()
    Subject(id='2229', name='China--History--Tiananmen Square Incident, 1989', uri='/srv/subject/2229.json', value='China--History--Tiananmen Square Incident, 1989', endpoint='subject')


    >>> collection = digitalarchive.Collection.match(name="Local Nationalism in Xinjiang").first()
    >>> docs = digitalarchive.Document.match(collections=[collection])
    >>> for doc in docs.all():
    ...     print doc.title
    Memorandum on a Discussion held by the Consul-General of the USSR in Ürümchi, G.S. DOBASHIN, with the Secretary of the Party Committee of the Xinjiang Uyghur Autonomous Region, Comrade LÜ JIANREN
    Memorandum on a Discussion held by the Consul-General of the USSR in Ürümchi, G.S. DOBASHIN, with Deputy Chairman of the People’s Committee of the Xinjiang Uyghur Autonomous Region, Comrade XIN LANTING
    Memorandum of a Discussion held by USSR Consul-General in Ürümchi, G S. Dobashin, with First Secretary of the Party Committee of the Xinjiang Uyghur Autonomous Region, Comrade Wang Enmao, and Chair of the People’s Committee, Comrade S. Äzizov
    Note from G. Dobashin, Consul-General of the USSR in Ürümchi, to Comrades N.T. Fedorenko, Zimianin, and P.F. Iudin
    Memorandum on a Discussion with Wang Huangzhang, Head of the Foreign Affairs Office of the Prefectural People's Committee
    Iu. Andropov to the Central Committee of the CPSU, 'On the Struggle with Local Nationalism in China'
    Note, M. Zimianin to the Central Committee of the CPSU and to Comrade Iu. V. Andropov
    M. Zimianin to the Central Committee of the CPSU and to Comrade Iu. V. Andropov, 'On Manifestations of Local Nationalism in Xinjiang (PRC)'
    M. Zimianin to the Department of the Central Committee of the CPSU and to Comrade Iu. V. Andropov

Contents
--------
.. toctree::
   :maxdepth: 2
   Quickstart
   Cookbooks
   API

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _Wilson Center's Digital Archive: https://digitalarchive.wilsoncenter.org/
.. _pip: https://pip.pypa.io/
