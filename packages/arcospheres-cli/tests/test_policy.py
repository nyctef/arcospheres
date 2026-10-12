import unittest
from unittest.mock import patch

from arcospheres_cli.arcoset import ArcoSet
from arcospheres_cli.policy import simplify_combinators
from arcospheres_cli.recipe import Recipe
from arcospheres_cli.simulate import validate_combinators


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.chance_recipes = [
            Recipe.from_str("X -> G", 20),
            Recipe.from_str("X -> Z", 20),
        ]
        self.ready = {ArcoSet.from_str("EX")}

    def test_simplification_removes_redundant_guards_without_mutating_inputs(self):
        recipes = [Recipe.from_str("G -> X", 10), Recipe.from_str("Z -> X", 10)]
        order = [0, 1]
        built = [["E", "EE"], ["E"]]
        production = ["E"]

        with patch("arcospheres_cli.simulate.RECIPES", recipes):
            priority, reduced, chance_clauses = simplify_combinators(
                self.chance_recipes, self.ready, order, built, production
            )
            self.assertEqual(reduced, [[""], [""]])
            self.assertEqual(chance_clauses, [""])
            self.assertEqual(
                validate_combinators(
                    self.chance_recipes, self.ready, priority, reduced, chance_clauses
                ),
                (2, 1),
            )

        self.assertEqual(order, [0, 1])
        self.assertEqual(built, [["E", "EE"], ["E"]])
        self.assertEqual(production, ["E"])

    def test_validation_rejects_recovery_loops(self):
        recipes = [Recipe.from_str("G -> Z", 10), Recipe.from_str("Z -> G", 10)]

        with patch("arcospheres_cli.simulate.RECIPES", recipes):
            with self.assertRaisesRegex(AssertionError, "LOOP"):
                validate_combinators(
                    self.chance_recipes, self.ready, [0, 1], [[""], [""]], ["E"]
                )

    def test_validation_rejects_production_outside_the_ready_family(self):
        recipes = [Recipe.from_str("E -> X", 10)]

        with patch("arcospheres_cli.simulate.RECIPES", recipes):
            with self.assertRaisesRegex(AssertionError, "EARLY PRODUCTION"):
                validate_combinators(
                    self.chance_recipes, self.ready, [0], [[""]], [""]
                )

    def test_validation_requires_production_at_every_ready_state(self):
        with self.assertRaisesRegex(AssertionError, "MISSED PRODUCTION"):
            validate_combinators(self.chance_recipes, self.ready, [], [], [])


if __name__ == "__main__":
    unittest.main()