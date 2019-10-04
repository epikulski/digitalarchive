

# Configure debug logging.
import logging
logging.basicConfig(level=logging.DEBUG)

# Pull an example Document.
# from digitalarchive.models import Document
# test_document = Document.match(name="soviet").first()
# test_doc_list = Document.match(name="soviet").all()
# test_document.pull()
# test_col = test_document.collections[0]
# print("barf")
#
# from digitalarchive.models import Document, Subject
# test_subject = Subject(id=2913, name="21st Century Committee for China-Japan Friendship")
# test_document = Document.match(subject=test_subject).first()
# test_doc_list = Document.match(subject=test_subject).all()
# test_document.pull()
# test_col = test_document.collections[0]
# print("barf")



# HTML Transcript hydration testing.
from digitalarchive.models import Document
test_doc = Document.match(id="176049").first()
test_doc.pull()
test_transcript =test_doc.transcripts[0]
test_transcript.hydrate()

# PDF transcript hydration testing
test_doc = Document.match(id="112566").first()
test_doc.pull()
test_transcript =test_doc.transcripts[0]
test_transcript.hydrate()
print("barf")


# Pull an Example Subject
# from digitalarchive.models import Subject
# test_subject = Subject.match(name="soviet")
# test_subject_first = test_subject.first()
# test_subject_all = test_subject.all()


print("End of script")