from plume import *
from tests.utils import DB_NAME

from contextlib import closing
import os
import unittest


class DatabaseAPITests(unittest.TestCase):

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
        class Pokemon(Model):
            name = TextField()
        
        self.assertFalse(self.table_exists(Pokemon))
        self.db.register(Pokemon)
        self.assertTrue(self.table_exists(Pokemon))

    def test_register_a_non_custom_model(self):
        # A error in table creation must raise an exception an must not make any change in the database.
        self.assertEqual(self.count_tables(), 0)
        
        with self.assertRaises(TypeError):
            self.db.register(object)
        
        self.assertEqual(self.count_tables(), 0)

    def test_register_several_custom_models(self):
        class Pokemon(Model):
            name = TextField()
        
        class Trainer(Model):
            name = TextField()
    
        self.assertEqual(self.count_tables(), 0)
        self.db.register(Pokemon, Trainer)
        self.assertTrue(self.table_exists(Pokemon))
        self.assertTrue(self.table_exists(Trainer))
        
    def test_store_a_database_reference_into_model_when_registered(self):
        class Pokemon(Model):
            name = TextField()

        self.db.register(Pokemon)
        try:
            Pokemon._db
        except AttributeError:
            self.fail()
            
    def test_no_database_reference_in_unregistered_model(self):
        class Pokemon(Model):
            name = TextField()

        with self.assertRaises(AttributeError):
            Pokemon._db

    def test_register_an_existing_table(self):
        class Pokemon(Model):
            name = TextField()

        self.db.register(Pokemon)
        try:
            self.db.register(Pokemon)
        except:
            self.fail()
        
    def test_all_model_fields_match_table_fields(self):
        class Pokemon(Model):
            name = TextField()
            level = IntegerField()
            size = FloatField()

        self.db.register(Pokemon)
        # Collect field names of the pokemon table
        db_fields = [ row[1] for row in 
            self.db._connection.execute('PRAGMA table_info(pokemon)').fetchall()
        ]
        
        self.assertEqual(len(db_fields), 4)
        for model_field in ['pk', 'name', 'level', 'size']:
            self.assertIn(model_field, db_fields)
            
    def tearDown(self):
        try:
            os.remove(DB_NAME)
        except:
            return

