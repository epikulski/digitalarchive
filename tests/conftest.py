import json
from pathlib import Path

from digitalarchive import models

import pytest

DATA_DIR = Path(Path(__file__).parent.absolute(), "data/")

@pytest.fixture
def mock_transcript():
    with Path(DATA_DIR, "transcript.json").open() as fd:
        transcript = json.load(fd)
    return models.Transcript(**transcript)


@pytest.fixture
def mock_collection():
    with Path(DATA_DIR, "collection.json").open() as fd:
        collection = json.load(fd)
    return models.Collection(**collection)
