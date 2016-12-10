# Plume:

## Description:

Plume is a single file, minimalist ORM for sqlite3 database.
It is not suited for production, and might never be.
Nevertheless, it aims to be an eductional support to 
python newcomer by keeping a codebase as clean as
possible. Moreover, it is my own way to improve my understanding on ORMs.

Plume only dependency is the Python Standard Library.

/!\ Some major API changes are about to come, the README is not up to date for now /!\
## Features:

1. Models to interact with tables in database.
2. QueryManager to enable SQL queries with a functional style.

## API:

### 1. Models:

A class-based interface to interact with a table in the database.
```python
class User(Model):
    username = TextField(max_length=30, unique=True)
    city     = TextField(max_length=100, required=False) 
    age      = IntegerField()
```
### 2. QueryManager:

#### Creating and instance:
```python
User.objects.create(city='Nantes', age=23)
or
user = User(city='Nantes', age=23)
user.save()
```
#### Creating several instances:
```python
users = User.bulk_create([user1, user2, user3])
```

#### Filtering:
```python
users = User.objects.filter(User.city == 'Nantes')

users = result = User.objects.filter(User.age > 18)

users = User.objects.filter(User.city == 'Nantes' |  User.city == 'Lyon')

users = User.objects.filter(User.city == 'Nantes' & User.age > 18)
```

#### Selecting: all field by default
```python
users = User.objects.all()
or
users = User.objects.select()
or
users = User.objects.select('*')

users = User.objects.select(User.name, User.age)

users = User.objects.select('name', 'age')
```

#### Ordering:
```python
users = User.objects.order_by(User.age, User.name)

users = User.objects.order_by('age', 'name')
```
