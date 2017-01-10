from plume import *
from plume.plume import UpdateQuery
from utils import Trainer

import pytest


class TestDeleteQuery:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            UpdateQuery(model=Trainer).__dict__

    def test_update_one_field_on_all_rows(self):
        pass
    
    def test_update_several_fields_on_all_rows(self):
        pass
        
    def test_update_one_field_with_subquery_on_all_rows(self):
        pass
    
    def test_update_one_field_with_filter(self):
        pass
    
    def test_update_several_fields_with_filter(self):
        pass
        
    def test_update_one_field_with_subquery_with_filter(self):
        pass

