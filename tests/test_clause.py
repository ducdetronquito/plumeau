import plume
from plume.plume import Clause
from utils import Pokemon

import pytest


class TestClause:
        
    def test_allows_or_operator_between_two_clauses(self):
        result = str((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
        expected = "( name = 'Charamander' OR name = 'Bulbasaur' )"
        assert result == expected

    def test_or_operator_between_two_clauses_add_brackets(self):
        result = str((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
        expected_open_bracket = '('
        expected_close_bracket = ')'
        assert result[0] == expected_open_bracket
        assert result[-1] == expected_close_bracket
        
    def test_allows_and_operator_between_two_clauses(self):
        result = str((Pokemon.name == 'Charamander') & (Pokemon.level == 18))
        expected = "name = 'Charamander' AND level = 18"
        assert result == expected
    
    def test_and_operator_between_two_clauses_does_not_add_brackets(self):
        result = str((Pokemon.name == 'Charamander') & (Pokemon.level == 18))
        assert result[0] != '('
        assert result[-1] != ')'

    def test_or_operator_has_lower_precedence_than_and_operator(self):
        result = str(
            (Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur')
            & (Pokemon.level > 18)
        )
        expected = "( name = 'Charamander' OR name = 'Bulbasaur' AND level > 18 )"
        assert result == expected

    def test_bracket_has_higher_precedence_than_and_operator(self):
        result = str(
            ((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
            & (Pokemon.level > 18)
        )
        expected = "level > 18 AND ( name = 'Charamander' OR name = 'Bulbasaur' )"
        assert result == expected
        
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Clause().__dict__
