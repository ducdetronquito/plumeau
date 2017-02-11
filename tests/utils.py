from plume.plume import ForeignKeyField, IntegerField, InsertQuery, Model, SQLiteDB, TextField


DB_NAME = ':memory:'


class Trainer(Model):
    name = TextField()
    age = IntegerField()


class Pokemon(Model):
    name = TextField()
    level = IntegerField()
    trainer = ForeignKeyField(Trainer, 'pokemons')


class BaseTestCase:

    TRAINERS = {
        'Giovanni': {
            'name': 'Giovanni',
            'age': 42
        },
        'James': {
            'name': 'James',
            'age': 21
        },
        'Jessie': {
            'name': 'Jessie',
            'age': 17
        },
    }

    POKEMONS = {
        'Kangaskhan': {
            'name': 'Kangaskhan',
            'level': 29,
            'trainer': 1
        },
        'Koffing': {
            'name': 'Koffing',
            'level': 9,
            'trainer': 2
        },
        'Wobbuffet': {
            'name': 'Wobbuffet',
            'level': 19,
            'trainer': 3
        },
    }

    def setup_method(self):
        self.db = SQLiteDB(DB_NAME)
        self.db.register(Trainer, Pokemon)

    def add_trainer(self, names):
        try:
            names = names.split()
        except:
            pass

        for name in names:
            InsertQuery(self.db).table(Trainer).from_dicts(self.TRAINERS[name]).execute()

    def add_pokemon(self, names):
        try:
            names = names.split()
        except:
            pass

        for name in names:
            InsertQuery(self.db).table(Pokemon).from_dicts(self.POKEMONS[name]).execute()
