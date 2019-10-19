"""Unit Tests of matching digitalarchive.matching."""
# pylint: disable=missing-function-docstring, no-self-use,too-few-public-methods


# 3rd Party Libraries
import pytest

# Application models
import digitalarchive.exceptions as exceptions
import digitalarchive.models as models


class TestResourceMatcher:
    """Test digitalarchive.matching.ResourceMatcher."""

    def test_invalid_keyword(self):
        with pytest.raises(exceptions.InvalidSearchField):
            models.Resource.match(test="test")
