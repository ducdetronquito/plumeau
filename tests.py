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

wario = User(name='Wario', age=42)
wario.size = 2.22
wario.save()

peach = User.objects.create(name="Peach", age=16, size=1.60)

queryset = User.objects.filter(User.age > 18, User.size > 1.80)

for instance in queryset:
    print(instance)
