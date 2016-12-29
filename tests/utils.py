from plume import Database, IntegerField, Model, TextField

import os
from sys import modules
import unittest

DB_NAME = ':memory:'

class Pokemon(Model):
    name = TextField()
    level = IntegerField()


class Trainer(Model):
    name = TextField()
    age = IntegerField()

