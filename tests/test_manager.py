from plume.plume import Database, Manager, Model, SelectQuery
from utils import DB_NAME, Pokemon, Trainer

import pytest


class TestManagerAPI:

    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Manager(Model).__dict__

    def test_is_accessible_as_Model_class_attribute(self):
        assert Trainer.objects is not None

    def test_is_not_accessible_as_Model_instance_attribute(self):
        with pytest.raises(AttributeError):
            Trainer().objects

    def test_filter_returns_a_queryset(self):
        assert isinstance(Trainer.objects.where(), SelectQuery)

    def test_select_returns_a_queryset(self):
        assert isinstance(Trainer.objects.select(), SelectQuery)


    def test_create_needs_named_parameters(self):
        with pytest.raises(TypeError):
            Trainer.objects.create('name', 'age')



