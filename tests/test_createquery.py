from plume.plume import CreateQuery, IntegerField, SQLiteDB, TextField

from utils import Trainer

import pytest


class TestCreateAPI:
    db = SQLiteDB(':memory:')

    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            CreateQuery(self.db).__dict__

    def test_attributes(self):
        expected = ('_db', '_fields', '_table')
        result = CreateQuery(self.db).__slots__
        assert result == expected

    def test_has_build_method(self):
        assert hasattr(CreateQuery(self.db), 'build') is True

    def test_has_execute_method(self):
        assert hasattr(CreateQuery(self.db), 'execute') is True

    def test_has_table_method(self):
        assert hasattr(CreateQuery(self.db), 'table') is True

    def test_has_fields_method(self):
        assert hasattr(CreateQuery(self.db), 'fields') is True

    def test_has_from_model_method(self):
        assert hasattr(CreateQuery(self.db), 'from_model') is True

    def test_has_str_method(self):
        assert hasattr(CreateQuery(self.db), '__str__') is True

class TestCreateQueries():

    db = SQLiteDB(':memory:')

    def test_can_output_raw_sql_query(self):
        query = CreateQuery(self.db).table('trainer').fields(
            TextField(name='name'),
            IntegerField(name='age')
        )
        result = query.build()
        expected = "CREATE TABLE IF NOT EXISTS trainer (age INTEGER NOT NULL, name TEXT NOT NULL)"
        assert result == expected


    def test_can_output_raw_sql_query_from_model(self):
        query = CreateQuery(self.db).from_model(Trainer)
        result = query.build()
        print(result)
        expected = (
            'CREATE TABLE IF NOT EXISTS trainer '
            '(age INTEGER NOT NULL, name TEXT NOT NULL, '
            'pk INTEGER PRIMARY KEY AUTOINCREMENT)'
        )
        assert result == expected

    def test_set_table_field_names(self):
        CreateQuery(self.db).table('trainer').fields(
            TextField(name='name'),
            IntegerField(name='age')
        ).execute()
        # Collect field names of the pokemon table
        db_fields = [ row[1] for row in
            self.db._connection.execute('PRAGMA table_info(trainer)').fetchall()
        ]

        assert len(db_fields) == 2

        for expected_field in ['name', 'age']:
            assert expected_field in db_fields

    def test_set_table_field_names_from_model(self):
        CreateQuery(self.db).from_model(Trainer).execute()
        # Collect field names of the pokemon table
        db_fields = [ row[1] for row in
            self.db._connection.execute('PRAGMA table_info(trainer)').fetchall()
        ]

        assert len(db_fields) == 2

        for expected_field in ['name', 'age']:
            assert expected_field in db_fields

# TODO: Check if field caracteristics are correct.
