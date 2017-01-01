from plume import *
from plume.plume import QuerySet
from utils import DB_NAME, Pokemon, Trainer

import pytest


class Base:
    
    TRAINERS = {
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
    
    POKEMONS = {
        'Kangaskhan': {
            'name': 'Kangaskhan',
            'level': 29,
            'trainer': 1
        },
        'Koffing': {
            'name': 'Koffing',
            'level': 9,
            'trainer': 2
        },
        'Wobbuffet': {
            'name': 'Wobbuffet',
            'age': 19,
            'trainer': 3
        },
    }
    
    def setup_method(self):
        db = Database(DB_NAME)
        db.register(Trainer, Pokemon)
    
    def add_trainer(self, names):
        try:
            names = names.split()
        except:
            pass
        
        for name in names:
            Trainer.objects.create(**self.TRAINERS[name])
            
    def add_pokemon(self, names):
        try:
            names = names.split()
        except:
            pass
        
        for name in names:
            Pokemon.objects.create(**self.POKEMONS[name])


class TestQuerySetAPI(Base):
    
    def test_output_queryset_as_string(self):
        result = str(Trainer.objects.filter(Trainer.age > 18, Trainer.name != 'Giovanni'))
        expected = "(SELECT * FROM trainer WHERE name != 'Giovanni' AND age > 18)"
        assert result == expected
        
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            QuerySet(Model).__dict__
            

class TestQuerySetSlice(Base):
    
    def test_indexed_access_to_first_element_returns_a_model_instance(self):
        self.add_trainer('Giovanni')
        trainer = Trainer.objects.filter()[0]
        assert trainer.name == 'Giovanni'
        assert trainer.age == 42
        
    def test_indexed_access_to_random_element_returns_a_model_instance(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainer = Trainer.objects.filter()[2]
        assert trainer.name == 'Jessie'
        assert trainer.age == 17
        
    def test_slice_access_with_start_and_stop_value_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = Trainer.objects.filter()[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17
        
    def test_slice_access_with_offset_only_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = Trainer.objects.filter()[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17
        
    def test_slice_access_with_offset_only_returns_a_pokemon_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = Trainer.objects.filter()[:2]
        assert len(trainers) == 2
        assert trainers[0].name == 'Giovanni'
        assert trainers[0].age == 42
        assert trainers[1].name == 'James'
        assert trainers[1].age == 21


class TestQuerySetResults(Base):
    
    def test_select_from_one_table_with_all_fields(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.filter())
        
        assert len(result) == 3
        giovanni, james, jessie = result
        
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        
        assert james.name == 'James'
        assert james.age == 21
        
        assert jessie.name == 'Jessie'
        assert jessie.age == 17
        
    def test_select_from_one_table_with_one_criterion(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.filter(Trainer.age > 18))
        assert len(result) == 2
        
        giovanni, james = result
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        
        assert james.name == 'James'
        assert james.age == 21
        
    def test_select_from_one_table_with_ANDs_criteria_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.filter((Trainer.age > 18)  & (Trainer.name != 'Giovanni')))
        assert len(result) == 1
        
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_select_from_one_table_with_ANDs_criteria_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.filter(Trainer.age > 18, Trainer.name != 'Giovanni'))
        assert len(result) == 1
        
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21
        
    def test_select_from_one_table_with_chained_filters(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        queryset = Trainer.objects.filter(Trainer.age > 18) 
        queryset.filter(Trainer.name != 'Giovanni')
        result = list(queryset)
        assert len(result) == 1
        
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21
        
    def test_select_from_one_table_with_in_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.filter(Trainer.age << [17, 21]))
        assert len(result) == 2
        
        james, jessie = result
        assert james.name == 'James'
        assert james.age == 21
        
        assert jessie.name == 'Jessie'
        assert jessie.age == 17
        
    def test_filter_on_one_field_must_returns_a_list_of_field_values(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.select('name'))
        expected = ['Giovanni', 'James', 'Jessie']
        
        assert result == expected
    
    def test_filter_on_several_fields_must_returns_a_list_of_namedtuples(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = list(Trainer.objects.select('name', 'age'))

        assert result[0][0] == 'Giovanni'
        assert result[0][1] == 42
        assert result[1][0] == 'James'
        assert result[1][1] == 21
        assert result[2][0] == 'Jessie'
        assert result[2][1] == 17

    def test_filter_on_table_with_related_field(self):
        self.add_trainer('Giovanni')
        self.add_pokemon('Kangaskhan')
        
        result = list(Pokemon.objects.filter())
        assert len(result) == 1
        
        pokemon = result[0]
        assert pokemon.name == 'Kangaskhan'
        assert pokemon.level == 29
        assert isinstance(result[0].trainer, Trainer) is True
        
        trainer = pokemon.trainer
        assert trainer.name == 'Giovanni'
        assert trainer.age == 42


