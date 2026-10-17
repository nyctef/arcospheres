from collections import Counter, defaultdict, deque
from typing import Literal

from attr import dataclass
from .arco_types import Graph
from .arcoset import ArcoSet
from .recipe import RECIPES, Recipe, get_common_input


def build_options(strategy: Graph) -> dict[ArcoSet, list[Recipe]]:
    # for every state we might pass through on the way to a chance-ready state, all the
    # recipes that make progress (get one step closer to the nearest chance-ready state)
    targets = {n[1] for n in strategy if n[0] == "chance"}
    starts = [n[1] for n in strategy if n[0] == "choice"]

    # successors: for each state, the full set of legal moves
    succ: dict[ArcoSet, list[tuple[Recipe, ArcoSet]]] = {}
    stack = list(starts)
    while stack:
        state = stack.pop()
        if state in succ:
            continue
        succ[state] = []
        if state in targets:
            continue
        for recipe in RECIPES:
            if recipe.can_apply(state):
                nxt = recipe.apply(state)
                succ[state].append((recipe, nxt))
                stack.append(nxt)

    # predecessors: inverse of the above
    preds: dict[ArcoSet, list[ArcoSet]] = defaultdict(list)
    for state, outs in succ.items():
        for _, nxt in outs:
            preds[nxt].append(state)
    dist = {t: 0 for t in targets if t in succ}
    queue: deque[ArcoSet] = deque(dist)
    while queue:
        state = queue.popleft()
        for pred in preds[state]:
            if pred not in dist:
                dist[pred] = dist[state] + 1
                queue.append(pred)

    # for each state, only the set of recipes that make progress towards one of `targets`.
    # avoids edges in `succ` that aren't useful.
    options: dict[ArcoSet, list[Recipe]] = {}
    pending = list(starts)
    while pending:
        state = pending.pop()
        if state in targets or state in options:
            continue
        options[state] = [r for r, n in succ[state] if dist.get(n) == dist[state] - 1]
        pending.extend(n for _, n in succ[state] if dist.get(n) == dist[state] - 1)
    return options


Clause = tuple[str, int]  # (extras text, bitmask of states it matches)


@dataclass
class CombinatorClause:
    leftsignal: str  # future: expand to union(signal, constant)
    comparison: Literal["=", ">="]  # ...
    rightconstant: int

    def __str__(self) -> str:
        return f"{self.leftsignal}{self.comparison}{self.rightconstant}"


@dataclass
class And:
    clauses: list[CombinatorClause]

    def __str__(self) -> str:
        return " AND ".join(str(c) for c in self.clauses)


@dataclass
class Or:
    clauses: list[And]

    def __str__(self) -> str:
        return " OR ".join(f"({a})" for a in self.clauses)


def build_policy(
    cube_ready: list[ArcoSet],
) -> Or:

    def to_and(ars: ArcoSet) -> And:
        counts = ars.as_dict()
        return And(
            [
                CombinatorClause(leftsignal=char, comparison="=", rightconstant=count)
                for char, count in counts.items()
                if count > 0
            ]
        )

    return Or([to_and(st) for st in cube_ready])


def print_combinators(
    chance_ready_recipes: list[Recipe],
    options: dict[ArcoSet, list[Recipe]],
    chance_ready: set[ArcoSet],
):
    chance_ready_mats = get_common_input(chance_ready_recipes)

    options_per_recipe: dict[Recipe, list[ArcoSet]] = defaultdict(list)
    for ars, recipes in options.items():
        # the `options` we're passed in from build_options should be all
        # the cases where picking that recipe makes progress, so for now
        # let's just pick one arbitrarily. can add back some more
        # optimization later.
        options_per_recipe[recipes[0]].append(ars)

    production_clauses = build_policy(list(sorted(chance_ready)))
    folding_clauses: dict[Recipe, Or] = {
        r: build_policy(options_per_recipe[r]) for r in options_per_recipe
    }
    print(f"  0. Production [needs {chance_ready_mats.txt()}]: {production_clauses}")
    for pos, (recipe, folding_clause) in enumerate(folding_clauses.items()):
        print(f"  {pos + 1}. {recipe} : {folding_clause}")


def format_combinator_part(c: str, req: str):
    if not len(c):
        return "(always)"

    counts = Counter(c)
    for ch in req:
        if ch in c:
            counts[ch] += 1
    return f"({' AND '.join(f'{ch} >= {counts[ch]}' for ch in sorted(counts))})"
