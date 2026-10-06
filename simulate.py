from arco_types import Graph, ArcoSet
from recipe import Recipe, RECIPES, get_common_input


def simulate_combinators(
    chance_recipes: list[Recipe],
    strategy: Graph,
    order: list[int],
    built: list[list[str]],
    chance_ready_clauses: list[str],
) -> None:

    chance_recipe_mats = get_common_input(chance_recipes)

    chance_ready = {n[1] for n in strategy if n[0] == "chance"}
    rules = [
        (RECIPES[ri], [recipe_in_plus(RECIPES[ri], c) for c in built[ri]])
        for ri in order
        if built[ri]
    ]

    chance_ready_patterns = [
        chance_recipe_mats.add(ArcoSet.from_str(c)) for c in chance_ready_clauses
    ]

    def should_produce(state: ArcoSet) -> bool:
        return any(state.contains(p) for p in chance_ready_patterns)

    def next_fold(state: ArcoSet) -> Recipe | None:
        for recipe, patterns in rules:
            if recipe.can_apply(state) and any(state.contains(p) for p in patterns):
                return recipe
        return None

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
                recipe = next_fold(state)
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
        f"Simulation OK: {len(chance_ready)} chance-ready states x 2 outcomes = {runs} runs, "
        f"all production exactly at chance-ready states (max {max_folds} folds)"
    )


def recipe_in_plus(recipe: Recipe, extras_txt: str) -> ArcoSet:
    return recipe.in_.add(ArcoSet.from_str(extras_txt))
