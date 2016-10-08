import os
from dumborm import *

try:
    os.remove('db_test.db')
except FileNotFoundError:
    pass

class User(Model):
    name = TextField(unique=True)
    age  = IntegerField()
    size = FloatField(required=False)

class Car(Model):
    name  = TextField()
    owner = ForeignKeyField(User, related_field='cars')
    

db = Database('db_test.db')

db.register(User)#, Car)

mario = User.objects.create(name='Mario', age=20, size=1.60)
print(mario.pk, mario.name, mario.age, mario.size)

luigi = User.objects.create(name='Luigi', age=23, size=1.83)
print(luigi.pk, luigi.name, luigi.age, luigi.size)

wario = User()
wario.name, wario.age, wario.size = 'Wario', 42, 1.53
wario.save()

mario.name = 'MarioBros'
mario.save()

"""
kart = Car.objects.create(name='Kart', owner=mario)
queryset = User.objects.where(User.name == 'Mario', User.age > 18)

for value in queryset:
    print(value)
"""

