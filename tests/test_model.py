from plume.plume import Manager, Model

from utils import Trainer

import pytest


class TestModel:
        
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
    
    def test_custom_model_is_sloted(self):
        sacha = Trainer(name='Sacha', age=42)
        
        with pytest.raises(AttributeError):
            sacha.__dict__


