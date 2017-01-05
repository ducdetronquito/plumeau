import plume
from utils import Pokemon

import pytest


class TestClause:

    def test_allows_or_operator_between_two_clauses(self):
        result = str((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
        expected = "name = 'Charamander' OR name = 'Bulbasaur'"
        assert result == expected

    def test_allows_and_operator_between_two_clauses(self):
        result = str((Pokemon.name == 'Charamander') & (Pokemon.level == 18))
        expected = "name = 'Charamander' AND level = 18"
        assert result == expected

    def test_or_operator_has_lower_precedence_than_and_operator(self):
        result = str(
            (Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur')
            & (Pokemon.level > 18)
        )
        expected = "name = 'Charamander' OR name = 'Bulbasaur' AND level > 18"
        assert result == expected

    def test_bracket_has_higher_precedence_than_and_operator(self):
        result = str(
            ((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
            & (Pokemon.level > 18)
        )
        expected = "name = 'Charamander' OR name = 'Bulbasaur' AND level > 18"
        assert result == expected
