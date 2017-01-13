from plume import Database, ForeignKeyField, IntegerField, Model, TextField


DB_NAME = ':memory:'


class Trainer(Model):
    name = TextField()
    age = IntegerField()


class Pokemon(Model):
    name = TextField()
    level = IntegerField()
    trainer = ForeignKeyField(Trainer, 'pokemons')

