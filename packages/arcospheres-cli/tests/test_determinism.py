import unittest

from arcospheres_cli.arcoset import ArcoSet
from arcospheres_cli.mdp import prune_mec
from arcospheres_cli.policy import build_combinators
from arcospheres_cli.recipe import RECIPES


class DeterminismTests(unittest.TestCase):
    def test_mec_nodes_have_canonical_order(self):
        chance = ("chance", ArcoSet.from_str("X"))
        choice = ("choice", ArcoSet.from_str("L"))
        graph = {choice: {chance: 1}, chance: {choice: "output"}}

        for nodes in ([choice, chance], [chance, choice]):
            with self.subTest(nodes=nodes):
                self.assertEqual(prune_mec(nodes, graph), [[chance, choice]])

    def test_split_mecs_have_canonical_order(self):
        chance_nodes = [("chance", ArcoSet.from_str(text)) for text in ("L", "X")]
        choice_nodes = [("choice", ArcoSet.from_str(text)) for text in ("E", "Z")]
        graph = {}
        for chance, choice in zip(chance_nodes, choice_nodes):
            graph[chance] = {choice: "output"}
            graph[choice] = {chance: 1}
        nodes = list(graph)

        self.assertEqual(prune_mec(nodes, graph), prune_mec(nodes[::-1], graph))

    def test_equal_scoring_clauses_ignore_candidate_order(self):
        allowed = [3] + [0] * (len(RECIPES) - 1)
        clauses = [("E", 1), ("Z", 2)]

        for ordered_clauses in (clauses, clauses[::-1]):
            with self.subTest(clauses=ordered_clauses):
                candidates = [ordered_clauses] + [[] for _ in RECIPES[1:]]
                result = build_combinators([0], allowed, candidates, 3)
                self.assertIsNotNone(result)
                self.assertEqual(result[0], ["Z", "E"])


if __name__ == "__main__":
    unittest.main()