from plume import *
from tests.utils import DB_NAME

import os
import unittest

class ManagerAPITests(unittest.TestCase):
    
    class Pokemon(Model):
        name = TextField()
            
    def setUp(self):
        db = Database(DB_NAME)
        db.register(self.Pokemon)
    
    def test_empty_filter_returns_all_tuple(self):
        self.Pokemon.objects.create(name='Charmander')
        self.Pokemon.objects.create(name='Bulbasaur')
        self.Pokemon.objects.create(name='Squirtle')
        self.assertEqual(len(list(self.Pokemon.objects.filter())), 3)
        
    def test_queryset_can_be_sliced(self):
        self.Pokemon.objects.create(name='Charmander')
        self.Pokemon.objects.create(name='Bulbasaur')
        self.Pokemon.objects.create(name='Squirtle')
        
        pokemon = self.Pokemon.objects.filter()[0:1]
        
        self.assertEqual(pokemon.name, 'Charmander')

    def tearDown(self):
        os.remove(DB_NAME)
