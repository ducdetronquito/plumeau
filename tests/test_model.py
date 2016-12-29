from plume.plume import Manager, Model

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

