Public API
**********

.. autoclass:: digitalarchive.models.Document(id, uri, title, description, doc_date, frontend_doc_date, slug, source_created_at, source_updated_at, first_published_at, source, type, rights, pdf_generated_at, date_range_start, sort_string_by_coverage, main_src, model, donors, subjects, transcripts, translations, media_files, languages, contributors, creators, original_coverages, collections, attachments, links, repositories, publishers, classifications)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Collection(id, name, slug, uri, parent, model, value, description, short_description, main_src, no_of_documents, is_inactive, source_created_at, source_updated_at, first_published_at)
   :members: hydrate, match

.. autoclass:: digitalarchive.models.Subject
   :members: hydrate, match


.. autoclass:: digitalarchive.models.UnhydratedField