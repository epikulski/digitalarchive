from digitalarchive.models import Document
test = "data"


test_subject = Document.match(name="soviet")
test_subject.pull()

print("End of script")