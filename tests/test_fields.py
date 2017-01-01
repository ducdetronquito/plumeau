from plume.plume import (Field, FloatField, IntegerField, PrimaryKeyField, TextField)

import pytest


class TestField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Field().__dict__


class TestFloatField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            FloatField().__dict__


class TestIntegerField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            IntegerField().__dict__


class TestPrimaryKeyField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            PrimaryKeyField().__dict__


class TestTextField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            TextField().__dict__


