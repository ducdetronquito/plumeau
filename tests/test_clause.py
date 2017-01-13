import plume
from utils import Pokemon

import pytest


class TestClause:

    def test_allows_or_operator_between_two_clauses(self):
        result = str((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
        expected = "pokemon.name = 'Charamander' OR pokemon.name = 'Bulbasaur'"
        assert result == expected

    def test_allows_and_operator_between_two_clauses(self):
        result = str((Pokemon.name == 'Charamander') & (Pokemon.level == 18))
        expected = "pokemon.name = 'Charamander' AND pokemon.level = 18"
        assert result == expected

    def test_or_operator_has_lower_precedence_than_and_operator(self):
        result = str(
            (Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur')
            & (Pokemon.level > 18)
        )
        expected = (
            "pokemon.name = 'Charamander' OR pokemon.name = 'Bulbasaur'"
            " AND pokemon.level > 18"
        )
        assert result == expected

    def test_bracket_has_higher_precedence_than_and_operator(self):
        result = str(
            ((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
            & (Pokemon.level > 18)
        )
        expected = (
            "pokemon.name = 'Charamander' OR pokemon.name = 'Bulbasaur'"
            " AND pokemon.level > 18"
        )
        assert result == expected
