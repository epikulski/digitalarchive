**********
Public API
**********

Models
======

Match-able & Hydrate-able Models
--------------------------------

.. autoclass:: digitalarchive.models.Document(id, uri, title, description, doc_date, frontend_doc_date, slug, source_created_at, source_updated_at, first_published_at, source, type, rights, pdf_generated_at, date_range_start, sort_string_by_coverage, main_src, model, donors, subjects, transcripts, translations, media_files, languages, contributors, creators, original_coverages, collections, attachments, links, repositories, publishers, classifications)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Collection(id, name, slug, uri, parent, model, value, description, short_description, main_src, no_of_documents, is_inactive, source_created_at, source_updated_at, first_published_at)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Subject(id, name, uri, value)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Coverage(id, name, uri, value, parent, children)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Contributor(id, name, value, uri)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Repository(id, name, value, uri)
   :members: hydrate, match

Hydrate-able Models
-------------------

.. autoclass:: digitalarchive.models.Transcript(id, filename, content_type, extension, asset_id, source_created_at, source_updated_at, url, html, pdf, raw)
   :members: hydrate

.. autoclass:: digitalarchive.models.Translation(id, filename, content_type, extension, asset_id, source_created_at, source_updated_at, url, html, pdf, raw, language)
   :members: hydrate

.. autoclass:: digitalarchive.models.MediaFile(id, filename, content_type, extension, asset_id, source_created_at, source_updated_at, path, html, pdf, raw)
   :members: hydrate

.. autoclass:: digitalarchive.models.Theme(id, slug, title, value, description, main_src, uri, featured_resources, has_map, has_timeline, featured_collections, dates_with_events)
   :members: hydrate

Other Models
------------

.. autoclass:: digitalarchive.models.Language(id, name)

.. autoclass:: digitalarchive.models.Donor(id, name)

.. autoclass:: digitalarchive.models.Type(id, name)

.. autoclass:: digitalarchive.models.Right(id, name)

.. autoclass:: digitalarchive.models.Classification(id, name)




,,,

.. autoclass:: digitalarchive.models.UnhydratedField


Matching
========

.. autoclass:: digitalarchive.matching.ResourceMatcher
   :members: first, all, hydrate