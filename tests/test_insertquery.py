from plume.plume import InsertQuery, SQLiteDB

from utils import BaseTestCase, Trainer

import pytest


class TestInsertQueryAPI:
    db = SQLiteDB(':memory:')

    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            InsertQuery(Trainer).__dict__

    def test_attributes(self):
        expected = ('_db', '_fields','_table', '_values')
        result = InsertQuery(self.db).__slots__
        assert result == expected

    def test_can_specify_fields_to_insert(self):
        assert hasattr(InsertQuery(self.db), 'fields') is True

    def test_can_specify_dict_values(self):
        assert hasattr(InsertQuery(self.db), 'from_dicts') is True

    def test_can_specify_table(self):
        assert hasattr(InsertQuery(self.db), 'table') is True

    def test_can_be_output_as_string(self):
        query = InsertQuery(self.db).table(Trainer).from_dicts({
            'name': 'Giovanni',
            'age': 42
        })
        expected = "(INSERT INTO trainer (age, name) VALUES (?, ?))"
        assert str(query) == expected

class TestInsertQueryResult(BaseTestCase):

    def test_can_insert_one_row_from_dict(self):
        ngiovanni = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni'"
        ).fetchone()
        assert ngiovanni[0] == 0

        InsertQuery(self.db).table(Trainer).from_dicts({
            'name': 'Giovanni',
            'age': 42
        }).execute()

        ngiovanni = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni'"
        ).fetchone()
        assert ngiovanni[0] == 1

    def test_can_insert_many_rows_from_dict(self):
        ntrainers = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni' OR name = 'James'"
        ).fetchone()
        assert ntrainers[0] == 0

        InsertQuery(self.db).table(Trainer).from_dicts([
            {'name': 'Giovanni', 'age': 42},
            {'name': 'James', 'age': 21}
        ]).execute()

        ngiovanni = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni' OR name = 'James'"
        ).fetchone()
        assert ngiovanni[0] == 2
