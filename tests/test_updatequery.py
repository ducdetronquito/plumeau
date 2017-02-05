from plume import *
from plume.plume import UpdateQuery
from utils import BaseTestCase, Trainer

import pytest


class TestUpdateQueryAPI:
    
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
        result = query.set(Trainer.age == 18)
        expected = '(UPDATE trainer SET age = 18)'
        assert str(result) == expected
        
    def test_updates_rules_can_be_chained(self):
        query = UpdateQuery(Trainer).set(Trainer.name == 'Giovanni')
        result = query.set(Trainer.age == 18)
        expected = "(UPDATE trainer SET name = 'Giovanni', age = 18)"
        assert str(result) == expected
        
    def test_can_output_selectquery_as_string(self):
        result = str(UpdateQuery(Trainer).set(Trainer.name == 'Jessie').where(Trainer.age < 18))
        expected = "(UPDATE trainer SET name = 'Jessie' WHERE trainer.age < 18)"
        assert result == expected

class TestUpdateQueryResult(BaseTestCase):
    
    def test_update_one_field_on_all_rows(self):
        self.add_trainer(['James', 'Jessie'])
        UpdateQuery(Trainer).set(Trainer.age == 42).execute()
        james, jessie = Trainer._db._connection.execute('SELECT age FROM trainer').fetchall()
        assert james[0] == 42
        assert jessie[0] == 42
        
    
    def test_update_several_fields_on_all_rows(self):
        self.add_trainer(['James', 'Jessie'])
        UpdateQuery(Trainer).set(Trainer.age == 42, Trainer.name == 'Giovanni').execute()
        james, jessie = Trainer._db._connection.execute('SELECT age, name FROM trainer').fetchall()
        assert james[0] == 42
        assert james[1] == 'Giovanni'
        assert jessie[0] == 42
        assert jessie[1] == 'Giovanni'
        
    def test_update_one_field_with_subquery_on_all_rows(self):
        self.add_trainer(['James', 'Jessie'])
        jessie_age = Trainer.select(Trainer.age).where(Trainer.name == 'Jessie')
        UpdateQuery(Trainer).set(Trainer.age == jessie_age).execute()
        james = Trainer._db._connection.execute("SELECT age FROM trainer WHERE name = 'James'").fetchall()
        assert james[0][0] == 17
    
    def test_update_one_field_with_filter(self):
        self.add_trainer(['James', 'Jessie'])
        UpdateQuery(Trainer).set(Trainer.age == 42).where(Trainer.name == 'Jessie').execute()
        james, jessie = Trainer._db._connection.execute('SELECT age FROM trainer').fetchall()
        assert james[0] == 21
        assert jessie[0] == 42
    
    def test_update_several_fields_with_filter(self):
        self.add_trainer(['James', 'Jessie'])
        (UpdateQuery(Trainer).set(Trainer.age == 42, Trainer.name == 'Giovanni')
            .where(Trainer.name == 'Jessie').execute())
        james, jessie = Trainer._db._connection.execute('SELECT age, name FROM trainer').fetchall()
        assert james[0] == 21
        assert james[1] == 'James'
        assert jessie[0] == 42
        assert jessie[1] == 'Giovanni'
        
    def test_update_one_field_with_subquery_with_filter(self):
        self.add_trainer(['James', 'Jessie'])
        jessie_name = Trainer.select(Trainer.name).where(Trainer.name == 'Jessie')
        UpdateQuery(Trainer).set(Trainer.age == 42).where(Trainer.name == jessie_name).execute()
        james, jessie = Trainer._db._connection.execute("SELECT age FROM trainer").fetchall()
        assert jessie[0] == 42
        assert james[0] == 21

