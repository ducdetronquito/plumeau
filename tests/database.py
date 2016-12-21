from plume import Database, Model
from tests.utils import DB_NAME, Pokemon, Trainer

from contextlib import closing
import os
from unittest import TestCase


class DatabaseAPITests(TestCase):

    def setUp(self):
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
        self.assertFalse(self.table_exists(Trainer))
        self.db.register(Trainer)
        self.assertTrue(self.table_exists(Trainer))

    def test_register_a_non_custom_model(self):
        # A error in table creation must raise an exception an must not make any change in the database.
        self.assertEqual(self.count_tables(), 0)
        
        with self.assertRaises(TypeError):
            self.db.register(object)
        
        self.assertEqual(self.count_tables(), 0)

    def test_register_several_custom_models(self):
        self.assertEqual(self.count_tables(), 0)
        self.db.register(Trainer, Pokemon)
        self.assertTrue(self.table_exists(Trainer))
        self.assertTrue(self.table_exists(Pokemon))
        
    def test_store_a_database_reference_into_model_when_registered(self):
        self.db.register(Trainer)
        try:
            Trainer._db
        except AttributeError:
            self.fail()
            
    def test_no_database_reference_in_unregistered_model(self):
        class CustomModel(Model):
            pass
        
        with self.assertRaises(AttributeError):
            CustomModel._db

    def test_register_an_existing_table(self):
        self.db.register(Trainer)
        try:
            self.db.register(Trainer)
        except:
            self.fail()
        
    def test_all_model_fields_match_table_fields(self):
        self.db.register(Trainer)
        # Collect field names of the pokemon table
        db_fields = [ row[1] for row in 
            self.db._connection.execute('PRAGMA table_info(trainer)').fetchall()
        ]
        
        self.assertEqual(len(db_fields), 3)
        for model_field in ['pk', 'name', 'age']:
            self.assertIn(model_field, db_fields)
            
    def tearDown(self):
        try:
            os.remove(DB_NAME)
        except:
            return

