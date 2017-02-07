from plume.plume import InsertQuery

from utils import BaseTestCase, Trainer

import pytest


class TestInsertQueryAPI:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            InsertQuery(Trainer).__dict__

    def test_attributes(self):
        expected = ('_fields', '_model', '_table', '_values')
        result = InsertQuery(Trainer).__slots__
        assert result == expected

    def test_can_specify_fields_to_insert(self):
        assert hasattr(InsertQuery(Trainer), 'with_fields') is True

    def test_can_specify_dict_values(self):
        assert hasattr(InsertQuery(Trainer), 'from_dicts') is True

    def test_can_be_output_as_string(self):
        query = InsertQuery(Trainer).from_dicts({
            'name': 'Giovanni',
            'age': 42
        })
        expected = "(INSERT INTO trainer (name, age) VALUES (?, ?))"
        assert str(query) == expected
        
class TestInsertQueryResult(BaseTestCase):
    
    def test_can_insert_one_row_from_dict(self):
        ngiovanni = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni'"
        ).fetchone()
        assert ngiovanni[0] == 0
        
        InsertQuery(Trainer).from_dicts({
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
        
        InsertQuery(Trainer).from_dicts([
            {'name': 'Giovanni', 'age': 42},
            {'name': 'James', 'age': 21}
        ]).execute()
        
        ngiovanni = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni' OR name = 'James'"
        ).fetchone()
        assert ngiovanni[0] == 2
