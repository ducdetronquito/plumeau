from plume import Database
from utils import DB_NAME, Pokemon, Trainer

import pytest

class TestDropTable:

    def test_drop_uncreated_table(self):
        db = Database(DB_NAME)
        db.drop_table(Trainer)

    def test_drop_table(self):
        db = Database(DB_NAME)
        db.register(Trainer)
        db.drop_table(Trainer)

    def test_drop_table_with_foreign_keys(self):
        db = Database(DB_NAME)
        db.register(Trainer, Pokemon)
        db.drop_table(Pokemon)


