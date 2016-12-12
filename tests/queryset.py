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
        
        self.Pokemon.objects.create(name='Charmander')
        self.Pokemon.objects.create(name='Bulbasaur')
        self.Pokemon.objects.create(name='Squirtle')
        
    def test_indexed_access_to_first_element_returns_a_pokemon_instance(self):
        pokemon = self.Pokemon.objects.filter()[0]
        self.assertEqual(pokemon.name, 'Charmander')
        
    def test_indexed_access_to_random_element_returns_a_pokemon_instance(self):
        pokemon = self.Pokemon.objects.filter()[2]
        self.assertEqual(pokemon.name, 'Squirtle')
        
    def test_slice_access_with_start_and_stop_value_returns_a_pokemon_list(self):
        pokemons = self.Pokemon.objects.filter()[1:3]
        self.assertEqual(len(pokemons), 2)
        self.assertEqual(pokemons[0].name, 'Bulbasaur')
        self.assertEqual(pokemons[1].name, 'Squirtle')
        
    def test_slice_access_with_offset_only_returns_a_pokemon_list(self):
        pokemons = self.Pokemon.objects.filter()[1:]
        self.assertEqual(len(pokemons), 2)
        self.assertEqual(pokemons[0].name, 'Bulbasaur')
        self.assertEqual(pokemons[1].name, 'Squirtle')
        
    def test_slice_access_with_offset_only_returns_a_pokemon_list(self):
        pokemons = self.Pokemon.objects.filter()[:2]
        self.assertEqual(len(pokemons), 2)
        self.assertEqual(pokemons[0].name, 'Charmander')
        self.assertEqual(pokemons[1].name, 'Bulbasaur')

    def tearDown(self):
        os.remove(DB_NAME)
