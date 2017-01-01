from plume.plume import Database, Manager, Model

from utils import DB_NAME, Pokemon, Trainer

import pytest
import sqlite3

class TestModel:
    
    def test_custom_model_is_sloted(self):
        sacha = Trainer(name='Sacha', age=42)
        
        with pytest.raises(AttributeError):
            sacha.__dict__
        
    def test_fieldnames_class_attribute_contains_primary_key_field_name(self):
        assert len(Model._fieldnames) == 1
        assert 'pk' in Model._fieldnames
        
    def test_objects_attribute_links_to_a_class_specific_manager(self):
        assert isinstance(Model.objects, Manager) is True
        assert Model.__name__ == Model.objects._model.__name__
        
    def test_pk_field_is_empty_by_default_on_model_instance(self):
        assert Model().pk is None
    
    def test_pk_field_can_be_set_as_model_instance_init_param(self):
        m = Model(pk=1)
        assert Model.pk == 1
        
    def test_two_equivalent_models_are_equals(self):
        m1 = Model(pk=1)
        m2 = Model(pk=1)
        assert m1 == m2
        
    def test_two_different_models_are_not_equals(self):
        m1 = Model(pk=1)
        m2 = Model(pk=2)
        assert m1 != m2
        
    def test_model_is_sloted(self):
        m1 = Model(pk=1)
        
        with pytest.raises(AttributeError):
            m1.__dict__

    def test_create_from_manager_returns_an_instance_with_pk_set(self):
        db = Database(DB_NAME)
        db.register(Trainer)
        giovanni = Trainer.objects.create(name='Giovanni', age=42)
        assert giovanni.pk == 1
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        
    def test_create_from_manager_returns_an_instance_with_pk_set_to_next_available_id(self):
        db = Database(DB_NAME)
        db.register(Trainer)
        giovanni = Trainer.objects.create(name='Giovanni', age=42)
        james = Trainer.objects.create(name='James', age=21)
        assert giovanni.pk == 1
        assert james.pk == 2

    def test_create_from_manager_allows_model_instance_as_parameter_for_foreign_key_field(self):
        db = Database(DB_NAME)
        db.register(Trainer, Pokemon)
        
        james = Trainer.objects.create(name='James', age=21)
        meowth = Pokemon.objects.create(name='Meowth', level=19, trainer=james)
        
        assert james.pk == 1
        assert meowth.trainer.pk == james.pk
        
    def test_create_from_manager_checks_for_integrity(self):
        db = Database(DB_NAME)
        db.register(Trainer, Pokemon)
        
        james = Trainer.objects.create(name='James', age=21)
        
        with pytest.raises(sqlite3.IntegrityError):
            Pokemon.objects.create(name='Meowth', level=19, trainer=2)
        
        


