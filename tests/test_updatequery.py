from plume import *
from plume.plume import UpdateQuery
from utils import BaseTestCase, Trainer

import pytest


class TestUpdateQueryAPI(BaseTestCase):
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            UpdateQuery(Trainer).__dict__
    
    def test_attributes(self):
        expected = ('_model', '_table', '_set')
        result = UpdateQuery(Trainer).__slots__
        assert result == expected
        
    def test_is_filterable(self):
        assert hasattr(UpdateQuery(Trainer), 'where') is True
    
    def test_can_set_updates_rules(self):
        query = UpdateQuery(Trainer)
        assert hasattr(query, 'set') is True
        q = query.set(Trainer.age == 18)
        print(str(q))
        q.execute()
        
    def test_updates_rules_can_be_chained(self):
        assert (
            '[NEED FIX] Provide a Class to handle (Expression, Expression, Expression)'
        ) is False
        query = UpdateQuery(Trainer).set(Trainer.name == 'Mario')
        query.set(Trainer.age == 18).execute()
    
    def test_can_output_selectquery_as_string(self):
        result = str(UpdateQuery(Trainer).set(Trainer.name == 'Newbie').where(Trainer.age < 18))
        assert (
            '[NEED FIX] Provide a Class to handle (Expression, Expression, Expression)'
        ) is False
        expected = "(UPDATE trainer SET trainer.name = 'Newbie' WHERE trainer.age > 18)"
        assert result == expected

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

