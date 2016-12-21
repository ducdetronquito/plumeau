from plume import Database, IntegerField, Model, TextField

import os
from sys import modules
import unittest

DB_NAME = ':memory:'

class Pokemon(Model):
    name = TextField()
    level = IntegerField()


class Trainer(Model):
    name = TextField()
    age = IntegerField()


class TestCase(unittest.TestCase):
            
    def setUp(self):
        db = Database(DB_NAME)
        
        for model in self.FIXTURES.get('models', ()):
            db.register(model)
        
        
    def add_fixture(self, model_class, values):
        
        model_name = model_class.__name__.lower()

        for value in values:
            model_class.objects.create(**self.FIXTURES[model_name][value])
            
