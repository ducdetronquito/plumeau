from plume import Database, Model
from utils import DB_NAME, Pokemon, Trainer

from contextlib import closing
import os
import pytest


class TestDatabaseAPI:

    def setup_method(self):
        self.db = Database(DB_NAME)
    
    def table_exists(self, model):
        with closing(self.db._connection.cursor()) as cursor:
            query = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(model.__name__.lower())
            )
            return bool(len(query.fetchall()))

    def count_tables(self):
        with closing(self.db._connection.cursor()) as cursor:
            query = cursor.execute("SELECT count(*) as number FROM sqlite_master WHERE type='table'").fetchall()
            return query[0][0]

    def test_register_a_custom_model(self):
        assert self.table_exists(Trainer) == False
        self.db.register(Trainer)
        assert self.table_exists(Trainer) == True

    def test_register_a_non_custom_model(self):
        # A error in table creation must raise an exception an must not make any change in the database.
        assert self.count_tables() == 0
        
        with pytest.raises(TypeError):
            self.db.register(object)
        
        assert self.count_tables() == 0

    def test_register_several_custom_models(self):
        assert self.count_tables() == 0
        self.db.register(Trainer, Pokemon)
        assert self.table_exists(Trainer) == True
        assert self.table_exists(Pokemon) == True
        
    def test_store_a_database_reference_into_model_when_registered(self):
        self.db.register(Trainer)
        try:
            Trainer._db
        except AttributeError:
            pytest.fail()
            
    def test_no_database_reference_in_unregistered_model(self):
        class CustomModel(Model):
            pass
        
        with pytest.raises(AttributeError):
            CustomModel._db

    def test_register_an_existing_table(self):
        self.db.register(Trainer)
        try:
            self.db.register(Trainer)
        except:
            pytest.fail()
        
    def test_all_model_fields_match_table_fields(self):
        self.db.register(Trainer)
        # Collect field names of the pokemon table
        db_fields = [ row[1] for row in 
            self.db._connection.execute('PRAGMA table_info(trainer)').fetchall()
        ]
        
        assert len(db_fields) == 3

        for model_field in ['pk', 'name', 'age']:
            assert model_field in db_fields
            
    def teardown_method(self):
        try:
            os.remove(DB_NAME)
        except:
            return

