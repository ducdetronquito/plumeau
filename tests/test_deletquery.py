from plume import *
from plume.plume import DeleteQuery
from utils import Trainer

import pytest


class TestDeleteQuery:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            DeleteQuery(model=Trainer).__dict__

    def test_delete_all_rows(self):
        pass
    
    def test_delete_with_one_filter(self):
        pass
    
    def test_delete_with_several_filters(self):
        pass

