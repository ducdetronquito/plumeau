from plume.plume import (
    CreateQuery, DeleteQuery, DropQuery, InsertQuery, Model,
    SelectQuery, SQLiteDB, UpdateQuery
)
from utils import DB_NAME, Pokemon, Trainer

from contextlib import closing
import os
import pytest


class TestSQLiteDBAPI:

    def setup_method(self):
        self.db = SQLiteDB(':memory:')

    def table_exists(self, model):
        with closing(self.db._connection.cursor()) as cursor:
            query = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(model.__name__.lower())
            )
            return bool(len(query.fetchall()))

    def count_tables(self):
        with closing(self.db._connection.cursor()) as cursor:
            query = cursor.execute("SELECT count(*) as number FROM sqlite_master WHERE type='table'").fetchall()
            return query[0][0]
            
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            self.db.__dict__
            
    def test_has_atomic_method(self):
        assert hasattr(self.db, 'atomic') is True

    def test_register_a_custom_model(self):
        assert self.table_exists(Trainer) == False
        self.db.register(Trainer)
        assert self.table_exists(Trainer) == True

    def test_register_several_custom_models(self):
        assert self.count_tables() == 0
        self.db.register(Trainer, Pokemon)
        assert self.table_exists(Trainer) == True
        assert self.table_exists(Pokemon) == True

    def test_store_a_database_reference_into_model_when_registered(self):
        self.db.register(Trainer)
        try:
            Trainer._db
        except AttributeError:
            pytest.fail()

    def test_no_database_reference_in_unregistered_model(self):
        class CustomModel(Model):
            pass

        with pytest.raises(AttributeError):
            CustomModel._db

    def test_register_an_existing_table(self):
        self.db.register(Trainer)
        try:
            self.db.register(Trainer)
        except:
            pytest.fail()

    def test_pragma_foreign_key_is_on(self):
        result = self.db._connection.execute('PRAGMA foreign_keys').fetchone()[0]
        assert result == 1

    def teardown_method(self):
        try:
            os.remove(DB_NAME)
        except:
            return


class TestSQLiteDBCreateQueryBuilder:
    db = SQLiteDB(':memory:')
    
    def test_create_returns_a_CreateQuery(self):
        assert isinstance(self.db.create(), CreateQuery) is True
        
    def test_create_from_model(self):
        query = self.db.create().from_model(Trainer)
        expected = (
            "CREATE TABLE IF NOT EXISTS trainer (age INTEGER NOT NULL, "
            "name TEXT NOT NULL, pk INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        assert self.db.build_create(query) == expected


class TestSQLiteDBDeleteQueryBuilder:
    db = SQLiteDB(':memory:')
    
    def test_delete_returns_a_DeleteQuery(self):
        assert isinstance(self.db.delete(), DeleteQuery) is True

    def test_delete_all_rows(self):
        query = self.db.delete().table(Trainer)
        expected = 'DELETE FROM trainer'
        assert self.db.build_delete(query) == expected

    def test_delete_filtered_rows(self):
        query = self.db.delete().table(Trainer).where(Trainer.name == 'Giovanni')
        expected = "DELETE FROM trainer WHERE trainer.name = 'Giovanni'"
        assert self.db.build_delete(query) == expected


class TestSQLiteDBDropQueryBuilder:
    db = SQLiteDB(':memory:')
    
    def test_drop_returns_a_DropQuery(self):
        assert isinstance(self.db.drop(), DropQuery) is True

    def test_drop_a_table(self):
        query = self.db.drop(Trainer)
        expected = 'DROP TABLE IF EXISTS trainer'
        assert self.db.build_drop(query) == expected


class TestSQLiteDBInsertQueryBuilder:
    db = SQLiteDB(':memory:')
    
    def test_insert_returns_a_InsertQuery(self):
        assert isinstance(self.db.insert(), InsertQuery) is True


    def test_update_one_row_from_dicts(self):
        query = self.db.insert().from_dicts({
            'name': 'Giovanni',
            'age': 42
        }).table(Trainer)
        expected = "INSERT INTO trainer (age, name) VALUES (?, ?)"
        assert self.db.build_insert(query) == expected


class TestSQLiteDBSelectQueryBuilder:
    db = SQLiteDB(':memory:')
    
    def test_select_returns_a_SelectQuery(self):
        assert isinstance(self.db.select(), SelectQuery) is True
    
    def test_select_from_one_table_with_all_fields(self):
        query = self.db.select().tables(Trainer)
        expected = 'SELECT * FROM trainer'
        assert self.db.build_select(query) == expected
    
    def test_select_from_several_tables_with_all_fields(self):
        query = self.db.select().tables(Trainer, Pokemon)
        expected = 'SELECT * FROM trainer, pokemon'
        assert self.db.build_select(query) == expected

    def test_select_from_one_table_with_several_fields(self):
        query = self.db.select(Trainer.name, Trainer.age).tables(Trainer)
        expected = 'SELECT trainer.name, trainer.age FROM trainer'
        assert self.db.build_select(query) == expected
        
    def test_select_from_one_table_with_one_criterion(self):
        query = self.db.select().tables(Trainer).where(Trainer.age > 18)
        expected = 'SELECT * FROM trainer WHERE trainer.age > 18'
        assert self.db.build_select(query) == expected
        
    def test_select_from_one_table_with_several_criteria(self):
        query = self.db.select().tables(Trainer).where(Trainer.age > 18, Trainer.name == 'Giovanni')
        expected = "SELECT * FROM trainer WHERE trainer.name = 'Giovanni' AND trainer.age > 18"
        assert self.db.build_select(query) == expected
        
    def test_select_from_one_table_with_limit(self):
        query = self.db.select().tables(Trainer).limit(10)
        expected = 'SELECT * FROM trainer LIMIT 10'
        assert self.db.build_select(query) == expected

    def test_select_from_one_table_with_limit_and_offset(self):
        query = self.db.select().tables(Trainer).limit(10).offset(42)
        expected = 'SELECT * FROM trainer LIMIT 10 OFFSET 42'
        assert self.db.build_select(query) == expected


class TestSQLiteDBUpdateQueryBuilder:
    db = SQLiteDB(':memory:')
    
    def test_update_returns_a_UpdateQuery(self):
        assert isinstance(self.db.update(), UpdateQuery) is True
    
    def test_update_with_table_and_field(self):
        query = self.db.update(Trainer.name == 'Giovanni').table(Trainer)
        expected = "UPDATE trainer SET name = 'Giovanni'"
        assert self.db.build_update(query) == expected

    def test_update_with_table_and_fields(self):
        query = self.db.update(Trainer.name == 'Giovanni', Trainer.age == 18).table(Trainer)
        expected = "UPDATE trainer SET name = 'Giovanni', age = 18"
        assert self.db.build_update(query) == expected
    
    def test_update_with_filters(self):
        query = self.db.update(Trainer.name == 'Giovanni').table(Trainer).where(Trainer.age > 18)
        expected = "UPDATE trainer SET name = 'Giovanni' WHERE trainer.age > 18"
        assert self.db.build_update(query) == expected




