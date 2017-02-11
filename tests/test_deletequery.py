from plume import *
from plume.plume import DeleteQuery, SelectQuery, SQLiteDB
from utils import BaseTestCase, Trainer

import pytest


class TestDeleteQueryAPI:
    db = SQLiteDB(':memory:')
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            DeleteQuery(self.db).__dict__

    def test_attributes(self):
        expected = ('_db', '_table')
        result = DeleteQuery(self.db).__slots__
        assert result == expected
        
    def test_is_filterable(self):
        assert hasattr(DeleteQuery(self.db), 'where') is True

    def test_can_output_selectquery_as_string(self):
        result = str(DeleteQuery(self.db).table(Trainer).where(Trainer.age > 18))
        expected = '(DELETE FROM trainer WHERE trainer.age > 18)'
        assert result == expected
    

class TestDeleteQueryWhere(BaseTestCase):
    
    def test_delete_all_rows(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        nrows = Trainer._db._connection.execute('SELECT count(*) FROM trainer').fetchone()[0]
        assert nrows == 3
        DeleteQuery(self.db).table(Trainer).execute()
        nrows = Trainer._db._connection.execute(
            "SELECT count(*) FROM trainer WHERE name != 'Giovanni'"
        ).fetchone()[0]
        assert nrows == 0
        
    def test_delete_with_filter(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        nrows = Trainer._db._connection.execute('SELECT count(*) FROM trainer').fetchone()[0]
        assert nrows == 3
        DeleteQuery(self.db).table(Trainer).where(Trainer.name == 'Giovanni').execute()
        nrows = Trainer._db._connection.execute(
            "SELECT count(*) FROM trainer WHERE name != 'Giovanni'"
        ).fetchone()[0]
        assert nrows == 2
    
    def test_filter_with_subquery(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        nrows = Trainer._db._connection.execute('SELECT count(*) FROM trainer').fetchone()[0]
        assert nrows == 3
        giovanni_name = SelectQuery(self.db).tables(Trainer).select(Trainer.name).where(Trainer.name == 'Giovanni')
        DeleteQuery(self.db).table(Trainer).where(Trainer.name == giovanni_name).execute()
        nrows = Trainer._db._connection.execute(
            "SELECT count(*) FROM trainer WHERE name != 'Giovanni'"
        ).fetchone()[0]
        assert nrows == 2

