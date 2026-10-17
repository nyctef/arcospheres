from .arco_types import Graph, ArcoSet, Or
from .recipe import Recipe


def simulate_combinators(
    chance_recipes: list[Recipe], strategy: Graph, rules: dict[Recipe, Or]
) -> None:

    chance_ready = {n[1] for n in strategy if n[0] == "chance"}

    def should_produce(state: ArcoSet) -> bool:
        return next_recipe(state) in chance_recipes

    def next_recipe(state: ArcoSet) -> Recipe | None:
        result = None
        for recipe, combinator_clause in rules.items():
            if combinator_clause.is_satisfied_by(state):
                assert recipe.can_apply(
                    state
                ), f"Combinator clause satisfied but recipe cannot apply at {state}"
                assert (
                    result is None
                ), f"Multiple combinator clauses satisfied for state {state}"
                result = recipe
        assert result is not None, f"No combinator clause satisfied for state {state}"
        return result

    runs = 0
    max_folds = 0
    for start in chance_ready:
        for chance_recipe in chance_recipes:
            state = chance_recipe.apply(start)
            visited = {state}
            folds = 0
            while True:
                if should_produce(state):
                    assert (
                        state in chance_ready
                    ), f"EARLY PRODUCTION: chance rule fires at off-plan {state} (from {start})"
                    break
                assert (
                    state not in chance_ready
                ), f"MISSED PRODUCTION: chance rule silent at chance-ready {state} (from {start})"
                recipe = next_recipe(state)
                assert (
                    recipe is not None
                ), f"STUCK: no rule fires at {state} (came from {start} via {chance_recipe})"
                state = recipe.apply(state)
                folds += 1
                assert state not in visited, f"LOOP: revisited {state} from {start}"
                visited.add(state)
            runs += 1
            max_folds = max(max_folds, folds)
    print(
        f"Simulation OK: {len(chance_ready)} chance-ready states x {len(chance_recipes)} outcomes = {runs} runs, "
        f"all production exactly at chance-ready states (max {max_folds} folds)"
    )


def recipe_in_plus(recipe: Recipe, extras_txt: str) -> ArcoSet:
    return recipe.in_.add(ArcoSet.from_str(extras_txt))
