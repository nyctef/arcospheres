from arco_types import Graph, ArcoSet
from recipe import Recipe, RECIPES

# TODO
CUBE_INPUT = ArcoSet.from_str("LXZ")


def simulate_combinators(
    strategy: Graph,
    order: list[int],
    built: list[list[str]],
    cube_clauses: list[str],
) -> None:
    cube_ready = {n[1] for n in strategy if n[0] == "chance"}
    cubes = [Recipe.from_str("LXZ -> PET", 20), Recipe.from_str("LXZ -> POG", 20)]
    rules = [
        (RECIPES[ri], [recipe_in_plus(RECIPES[ri], c) for c in built[ri]])
        for ri in order
        if built[ri]
    ]

    cube_patterns = [CUBE_INPUT.add(ArcoSet.from_str(c)) for c in cube_clauses]

    def should_cube(state: ArcoSet) -> bool:
        return any(state.contains(p) for p in cube_patterns)

    def next_fold(state: ArcoSet) -> Recipe | None:
        for recipe, patterns in rules:
            if recipe.can_apply(state) and any(state.contains(p) for p in patterns):
                return recipe
        return None

    runs = 0
    max_folds = 0
    for start in cube_ready:
        for cube in cubes:
            state = cube.apply(start)
            visited = {state}
            folds = 0
            while True:
                if should_cube(state):
                    assert (
                        state in cube_ready
                    ), f"EARLY CUBE: cube rule fires at off-plan {state} (from {start})"
                    break
                assert (
                    state not in cube_ready
                ), f"MISSED CUBE: cube rule silent at cube-ready {state} (from {start})"
                recipe = next_fold(state)
                assert (
                    recipe is not None
                ), f"STUCK: no rule fires at {state} (came from {start} via {cube})"
                state = recipe.apply(state)
                folds += 1
                assert state not in visited, f"LOOP: revisited {state} from {start}"
                visited.add(state)
            runs += 1
            max_folds = max(max_folds, folds)
    print(
        f"Simulation OK: {len(cube_ready)} cube-ready states x 2 outcomes = {runs} runs, "
        f"all cube exactly at cube-ready states (max {max_folds} folds)"
    )


def recipe_in_plus(recipe: Recipe, extras_txt: str) -> ArcoSet:
    return recipe.in_.add(ArcoSet.from_str(extras_txt))
