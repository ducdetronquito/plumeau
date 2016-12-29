from plume.plume import SQLiteAPI

import pytest


class TestSQLiteAPI:
    
    def test_select_from_one_table_with_all_fields(self):
        result = SQLiteAPI.select(tables='pokemon')
        expected = 'SELECT * FROM pokemon'
        assert result == expected
    
    def test_select_from_several_tables_with_all_fields(self):
        result = SQLiteAPI.select(tables=('pokemon', 'trainer'))
        expected = 'SELECT * FROM pokemon, trainer'
        assert result == expected

    def test_select_from_one_table_with_several_fields(self):
        result = SQLiteAPI.select(tables='pokemon', fields=('name', 'level'))
        expected = 'SELECT name, level FROM pokemon'
        assert result == expected
        
    def test_select_from_one_table_with_one_criterion(self):
        result = SQLiteAPI.select(tables='pokemon', where= 'level > 18')
        expected = 'SELECT * FROM pokemon WHERE level > 18'
        assert result == expected
        
        
    def test_select_from_one_table_with_several_criteria(self):
        result = SQLiteAPI.select(tables='pokemon', where="name = 'Pikachu' AND level > 18")
        expected = "SELECT * FROM pokemon WHERE name = 'Pikachu' AND level > 18"
        assert result == expected
        
    def test_select_from_one_table_with_count_and_offset(self):
        result = SQLiteAPI.select(tables='pokemon', count=10, offset=42)
        expected = 'SELECT * FROM pokemon LIMIT 10 OFFSET 42'
        assert result == expected
