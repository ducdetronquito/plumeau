from tests.utils import Trainer, TestCase


class TrainerTestCase(TestCase):
    FIXTURES = {
        'models': [Trainer],
        'trainer': {
            'Giovanni': {
                'name': 'Giovanni',
                'age': 42
            },
            'James': {
                'name': 'James',
                'age': 21
            },
            'Jessie': {
                'name': 'Jessie',
                'age': 17
            },
        }
    }


class QuerySetSliceTests(TrainerTestCase):
    
    def test_indexed_access_to_first_element_returns_a_model_instance(self):
        self.add_fixture(Trainer, ['Giovanni'])

        trainer = Trainer.objects.filter()[0]
        
        self.assertEqual(trainer.name, 'Giovanni')
        self.assertEqual(trainer.age, 42)
        
    def test_indexed_access_to_random_element_returns_a_model_instance(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        trainer = Trainer.objects.filter()[2]

        self.assertEqual(trainer.name, 'Jessie')
        self.assertEqual(trainer.age, 17)
        
    def test_slice_access_with_start_and_stop_value_returns_a_model_instance_list(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        trainers = Trainer.objects.filter()[1:3]
        
        self.assertEqual(len(trainers), 2)
        self.assertEqual(trainers[0].name, 'James')
        self.assertEqual(trainers[0].age, 21)
        self.assertEqual(trainers[1].name, 'Jessie')
        self.assertEqual(trainers[1].age, 17)
        
    def test_slice_access_with_offset_only_returns_a_model_instance_list(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        trainers = Trainer.objects.filter()[1:3]
        
        self.assertEqual(len(trainers), 2)
        self.assertEqual(trainers[0].name, 'James')
        self.assertEqual(trainers[0].age, 21)
        self.assertEqual(trainers[1].name, 'Jessie')
        self.assertEqual(trainers[1].age, 17)
        
    def test_slice_access_with_offset_only_returns_a_pokemon_list(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        trainers = Trainer.objects.filter()[:2]
        
        self.assertEqual(len(trainers), 2)
        self.assertEqual(trainers[0].name, 'Giovanni')
        self.assertEqual(trainers[0].age, 42)
        self.assertEqual(trainers[1].name, 'James')
        self.assertEqual(trainers[1].age, 21)
        

class QuerySetResultsTests(TrainerTestCase):
    
    def test_select_from_one_table_with_all_fields(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        result = list(Trainer.objects.filter())
        
        self.assertEqual(len(result), 3)
        giovanni, james, jessie = result
        
        self.assertEqual(giovanni.name, 'Giovanni')
        self.assertEqual(giovanni.age, 42)
        
        self.assertEqual(james.name, 'James')
        self.assertEqual(james.age, 21)
        
        self.assertEqual(jessie.name, 'Jessie')
        self.assertEqual(jessie.age, 17)
        
        

    def test_select_from_one_table_with_one_criterion(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        result = list(Trainer.objects.filter(Trainer.age > 18))
        
        self.assertEqual(len(result), 2)
        giovanni, james = result
        
        self.assertEqual(giovanni.name, 'Giovanni')
        self.assertEqual(giovanni.age, 42)
        
        self.assertEqual(james.name, 'James')
        self.assertEqual(james.age, 21)
        
        
    def test_select_from_one_table_with_several_criteria(self):
        self.add_fixture(Trainer, ['Giovanni', 'James', 'Jessie'])
        
        result = list(Trainer.objects.filter((Trainer.age > 18)  & (Trainer.name != 'Giovanni')))
        
        self.assertEqual(len(result), 1)
        james = result[0]
        
        self.assertEqual(james.name, 'James')
        self.assertEqual(james.age, 21)


