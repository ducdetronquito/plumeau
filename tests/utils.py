from plume import Database, IntegerField, Model, TextField

DB_NAME = ':memory:'

class Pokemon(Model):
    name = TextField()
    level = IntegerField()


class Trainer(Model):
    name = TextField()
    age = IntegerField()

