import unittest
from plume import *

class DatabaseTests(unittest.TestCase):
    
    class User(Model):
        name = TextField()

    db_name = 'test.db'

    def setUp(self):
        print("setup")

    def test_register_a_custom_model(self):
        
        DatabaseTests.User


    def test_register_a_non_custom_model(self):
        print("b")

    def test_register_several_custom_models(self):
        pass

    def test_store_a_database_reference_into_model_when_registered(self):
        pass

    def test_create_a_new_table(self):
        pass

    def test_create_an_existing_table(self):
        pass

    def test_create_table_with_model_name_as_table_name(self):
        pass

    def tearDown(self):
        try:
            os.remove('tests.db')
        except:
            return

if __name__ == '__main__':
    unittest.main()

