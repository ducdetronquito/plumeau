from plume import *
from plume.plume import SQLiteDB, UpdateQuery
from utils import BaseTestCase, Trainer

import pytest


class TestUpdateQueryAPI:
    db = SQLiteDB(':memory:')
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            UpdateQuery(db=self.db).__dict__
    
    def test_attributes(self):
        expected = ('_db', '_fields', '_table')
        result = UpdateQuery(db=self.db).__slots__
        assert result == expected
        
    def test_is_filterable(self):
        assert hasattr(UpdateQuery(db=self.db), 'where') is True
    
    def test_can_set_updates_rules(self):
        query = UpdateQuery(db=self.db).table(Trainer)
        assert hasattr(query, 'fields') is True
        query.fields(Trainer.age == 18)
        expected = 'UPDATE trainer SET age = 18'
        assert query.build() == expected
        
    def test_updates_rules_can_be_chained(self):
        query = UpdateQuery(db=self.db).table(Trainer).fields(Trainer.name == 'Giovanni')
        query.fields(Trainer.age == 18)
        expected = "UPDATE trainer SET name = 'Giovanni', age = 18"
        assert query.build() == expected
        
    def test_can_output_selectquery_as_string(self):
        query = UpdateQuery(db=self.db).table(Trainer).fields(Trainer.name == 'Jessie').where(Trainer.age < 18)
        expected = "(UPDATE trainer SET name = 'Jessie' WHERE trainer.age < 18)"
        assert str(query) == expected


class TestUpdateQueryResult(BaseTestCase):
    
    def test_update_one_field_on_all_rows(self):
        self.add_trainer(['James', 'Jessie'])
        UpdateQuery(db=self.db).table(Trainer).fields(Trainer.age == 42).execute()
        james, jessie = Trainer._db._connection.execute('SELECT age FROM trainer').fetchall()
        assert james[0] == 42
        assert jessie[0] == 42
        
    
    def test_update_several_fields_on_all_rows(self):
        self.add_trainer(['James', 'Jessie'])
        UpdateQuery(db=self.db).table(Trainer).fields(Trainer.age == 42, Trainer.name == 'Giovanni').execute()
        james, jessie = Trainer._db._connection.execute('SELECT age, name FROM trainer').fetchall()
        assert james[0] == 42
        assert james[1] == 'Giovanni'
        assert jessie[0] == 42
        assert jessie[1] == 'Giovanni'
        
    def test_update_one_field_with_subquery_on_all_rows(self):
        self.add_trainer(['James', 'Jessie'])
        jessie_age = Trainer.select(Trainer.age).where(Trainer.name == 'Jessie')
        UpdateQuery(db=self.db).table(Trainer).fields(Trainer.age == jessie_age).execute()
        james = Trainer._db._connection.execute("SELECT age FROM trainer WHERE name = 'James'").fetchall()
        assert james[0][0] == 17
    
    def test_update_one_field_with_filter(self):
        self.add_trainer(['James', 'Jessie'])
        UpdateQuery(db=self.db).table(Trainer).fields(Trainer.age == 42).where(Trainer.name == 'Jessie').execute()
        james, jessie = Trainer._db._connection.execute('SELECT age FROM trainer').fetchall()
        assert james[0] == 21
        assert jessie[0] == 42
    
    def test_update_several_fields_with_filter(self):
        self.add_trainer(['James', 'Jessie'])
        (UpdateQuery(db=self.db).table(Trainer).fields(Trainer.age == 42, Trainer.name == 'Giovanni')
            .where(Trainer.name == 'Jessie').execute())
        james, jessie = Trainer._db._connection.execute('SELECT age, name FROM trainer').fetchall()
        assert james[0] == 21
        assert james[1] == 'James'
        assert jessie[0] == 42
        assert jessie[1] == 'Giovanni'
        
    def test_update_one_field_with_subquery_with_filter(self):
        self.add_trainer(['James', 'Jessie'])
        jessie_name = Trainer.select(Trainer.name).where(Trainer.name == 'Jessie')
        UpdateQuery(db=self.db).table(Trainer).fields(Trainer.age == 42).where(Trainer.name == jessie_name).execute()
        james, jessie = Trainer._db._connection.execute("SELECT age FROM trainer").fetchall()
        assert jessie[0] == 42
        assert james[0] == 21

