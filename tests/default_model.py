import unittest

class DefaultModelTests(unittest.TestCase):
        
    def test_fieldnames_class_attribute_contains_primary_key_field_name(self):
        from plume import Model
        self.assertEqual(len(Model._fieldnames), 1)
        self.assertIn('pk', Model._fieldnames)
        
    def test_objects_attribute_links_to_a_class_specific_manager(self):
        from plume import Manager, Model
        self.assertTrue(isinstance(Model.objects, Manager))
        self.assertEqual(Model.__name__, Model.objects._model.__name__)
        
    def test_pk_field_is_empty_by_default_on_model_instance(self):
        from plume import Model
        self.assertIsNone(Model().pk)
    
    def test_pk_field_can_be_set_as_model_instance_init_param(self):
        from plume import Model
        m = Model(pk=1)
        self.assertEqual(Model.pk, 1)

