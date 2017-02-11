from plume.plume import DeleteQuery, DropQuery, SQLiteDB
from utils import Pokemon, Trainer

import pytest

class TestDropTableAPI:
    db = SQLiteDB(':memory:')
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            DeleteQuery(db=self.db).__dict__
    
    def test_attributes(self):
        expected = ('_db', '_table')
        result = DeleteQuery(db=self.db).__slots__
        assert result == expected
        
    def test_has_table_method(self):
        assert hasattr(DeleteQuery(db=self.db), 'table') is True

class TestDropTableResult:
    # TODO: Make Raw SQL queries to assert changes happened.
    def test_drop_uncreated_table(self):
        db = SQLiteDB(':memory:')
        DropQuery(db).table(Trainer).execute()

    def test_drop_table(self):
        db = SQLiteDB(':memory:')
        db.create().from_model(Trainer).execute()
        DropQuery(db).table(Trainer).execute()

    def test_drop_table_with_foreign_keys(self):
        db = SQLiteDB(':memory:')
        db.create().from_model(Trainer).execute()
        db.create().from_model(Pokemon).execute()
        DropQuery(db).table(Pokemon).execute()


