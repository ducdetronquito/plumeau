from plume import *
from tests.utils import Pokemon

from unittest import TestCase


class ClauseTests(TestCase):
        
    def test_allows_or_operator_between_two_clauses(self):
        clause = (Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur')
        
        self.assertEqual(
            "( name = 'Charamander' OR name = 'Bulbasaur' )",
            str(clause),
        )
        
    def test_or_operator_between_two_clauses_add_brackets(self):
        clause = (Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur')
        clause_str = str(clause)
        
        self.assertEqual(clause_str[0], '(')
        self.assertEqual(clause_str[-1], ')')
        
    def test_allows_and_operator_between_two_clauses(self):
        clause = (Pokemon.name == 'Charamander') & (Pokemon.level == 18)
        
        self.assertEqual(
            "name = 'Charamander' AND level = 18",
            str(clause),
        )
    
    def test_and_operator_between_two_clauses_does_not_add_brackets(self):
        clause = (Pokemon.name == 'Charamander') & (Pokemon.level == 18)
        clause_str = str(clause)
        
        self.assertNotEqual(clause_str[0], '(')
        self.assertNotEqual(clause_str[-1], ')')

    def test_or_operator_has_lower_precedence_than_and_operator(self):
        clause = (
            (Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur')
            & (Pokemon.level > 18)
        )
        
        self.assertEqual(
            "( name = 'Charamander' OR name = 'Bulbasaur' AND level > 18 )",
            str(clause),
        )

    def test_bracket_has_higher_precedence_than_and_operator(self):
        clause = (
            ((Pokemon.name == 'Charamander') | (Pokemon.name == 'Bulbasaur'))
            & (Pokemon.level > 18)
        )

        self.assertEqual(
            "level > 18 AND ( name = 'Charamander' OR name = 'Bulbasaur' )",
            str(clause),
        )
