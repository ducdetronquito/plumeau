from plume import SQLiteAPI

from unittest import TestCase


class SQLiteAPITests(TestCase):
    
    def test_select_from_one_table_with_all_fields(self):
        self.assertEqual(
            SQLiteAPI.select(tables='pokemon'),
            'SELECT * FROM pokemon',
        )
    
    def test_select_from_several_tables_with_all_fields(self):
        self.assertEqual(
            SQLiteAPI.select(tables=('pokemon', 'trainer')),
            'SELECT * FROM pokemon, trainer',
        )

    def test_select_from_one_table_with_several_fields(self):
        self.assertEqual(
            SQLiteAPI.select(tables='pokemon', fields=('name', 'level')),
            'SELECT name, level FROM pokemon',
        )
        
    def test_select_from_one_table_with_one_criterion(self):
        self.assertEqual(
            SQLiteAPI.select(tables='pokemon', where= 'level > 18'),
            'SELECT * FROM pokemon WHERE level > 18',
        )
        
        
    def test_select_from_one_table_with_several_criteria(self):
        self.assertEqual(
            SQLiteAPI.select(tables='pokemon', where='name = Pikachu AND level > 18'),
            'SELECT * FROM pokemon WHERE name = Pikachu AND level > 18',
        )
