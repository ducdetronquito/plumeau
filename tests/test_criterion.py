from plume.plume import Criterion, Field

import pytest


class TestCriterion:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Criterion(Field, '==', 'value').__dict__
