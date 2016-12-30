from plume.plume import Manager, Model

import pytest


class TestManagerAPI:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Manager(Model).__dict__
