from collections import Counter, defaultdict, deque
from typing import Callable
from itertools import combinations
from arco_types import Graph
from arcoset import ArcoSet
from recipe import RECIPES, Recipe, get_common_input


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


def build_combinators(
    order: list[int],
    allowed: list[int],
    candidates: list[list[Clause]],
    all_states: int,
) -> list[list[str]] | None:
    unhandled = all_states
    result: list[list[str]] = [[] for _ in RECIPES]
    for pos, ri in enumerate(order):
        later = 0
        for rj in order[pos + 1 :]:
            later |= allowed[rj]
        must = unhandled & allowed[ri] & ~later
        if not must:
            continue
        bad = unhandled & ~allowed[ri]
        valid = [(txt, m) for txt, m in candidates[ri] if not (m & bad)]
        max_by: Callable[[tuple[str, int]], tuple[int, int, int]] = lambda c: (
            (c[1] & must).bit_count(),
            (c[1] & unhandled).bit_count(),
            -len(c[0]),
        )
        while must:
            best = max(valid, key=max_by)
            if not (best[1] & must):
                return None
            result[ri].append(best[0])
            unhandled &= ~best[1]
            must &= ~best[1]
    return result if not unhandled else None


def build_cube_policy(
    chance_ready_recipes: list[Recipe],
    options: dict[ArcoSet, list[Recipe]],
    cube_ready: set[ArcoSet],
) -> list[str]:
    chance_recipe_mats = get_common_input(chance_ready_recipes)

    forbidden = [
        st for st in options if st.contains(chance_recipe_mats) and st not in cube_ready
    ]
    texts: set[str] = set()
    for st in cube_ready:
        extras_txt = st.remove(chance_recipe_mats).txt()
        for size in range(len(extras_txt) + 1):
            texts.update("".join(c) for c in combinations(extras_txt, size))

    def matches(st: ArcoSet, txt: str) -> bool:
        return st.contains(chance_recipe_mats.add(ArcoSet.from_str(txt)))

    valid = sorted(t for t in texts if not any(matches(f, t) for f in forbidden))
    uncovered = set(cube_ready)
    clauses: list[str] = []
    while uncovered:
        best = max(
            valid,
            key=lambda t: (sum(1 for st in uncovered if matches(st, t)), -len(t), t),
        )
        clauses.append(best)
        uncovered = {st for st in uncovered if not matches(st, best)}
    return clauses


def print_combinators(
    chance_ready_recipes: list[Recipe],
    options: dict[ArcoSet, list[Recipe]],
    chance_ready: set[ArcoSet],
) -> tuple[list[int], list[list[str]], list[str]]:
    import random

    chance_ready_mats = get_common_input(chance_ready_recipes)

    states = list(options)
    bit = {st: 1 << i for i, st in enumerate(states)}
    all_states = (1 << len(states)) - 1
    allowed = [0] * len(RECIPES)
    for st, rs in options.items():
        for r in rs:
            allowed[RECIPES.index(r)] |= bit[st]
    used = [ri for ri in range(len(RECIPES)) if allowed[ri]]

    candidates: list[list[Clause]] = [[] for _ in RECIPES]
    for ri in used:
        recipe = RECIPES[ri]
        by_mask: dict[int, str] = {}
        texts: set[str] = set()
        for st in states:
            if allowed[ri] & bit[st]:
                extras_txt = st.remove(recipe.in_).txt()
                for size in range(len(extras_txt) + 1):
                    texts.update("".join(c) for c in combinations(extras_txt, size))
        for txt in texts:
            pattern = recipe.in_.add(ArcoSet.from_str(txt))
            mask = 0
            for st in states:
                if st.contains(pattern):
                    mask |= bit[st]
            if mask not in by_mask or (len(txt), txt) < (
                len(by_mask[mask]),
                by_mask[mask],
            ):
                by_mask[mask] = txt
        candidates[ri] = [(txt, m) for m, txt in by_mask.items()]

    def cost(order: list[int]) -> tuple[int, int] | None:
        built = build_combinators(order, allowed, candidates, all_states)
        if built is None:
            return None
        return (
            sum(len(c) for c in built),
            sum(len(t) for c in built for t in c),
        )

    rng = random.Random(0)
    best_order: list[int] = []
    best_cost = (10**9, 10**9)
    for _ in range(25):
        order = used[:]
        rng.shuffle(order)
        current = cost(order)
        assert current is not None
        improved = True
        while improved:
            improved = False
            for i in range(len(order)):
                for j in range(len(order)):
                    if i == j:
                        continue
                    trial = order[:]
                    trial.insert(j, trial.pop(i))
                    c = cost(trial)
                    if c is not None and c < current:
                        order, current, improved = trial, c, True
        if current < best_cost:
            best_order, best_cost = order, current

    built = build_combinators(best_order, allowed, candidates, all_states)
    assert built is not None
    chance_ready_clauses = build_cube_policy(
        chance_ready_recipes, options, chance_ready
    )
    print(
        f"\nPriority order with {best_cost[0]} clauses total, "
        f"{best_cost[1]} extra-sphere literals ({len(states)} states), "
        f"plus {len(chance_ready_clauses)} clauses for when to produce:"
    )
    chance_ready_text = " OR ".join(
        format_combinator_part(c, chance_ready_mats.txt())
        for c in sorted(chance_ready_clauses)
    )
    print(f"  0. CHANCE LXZ [needs LXZ]: {chance_ready_text}")
    for pos, ri in enumerate(best_order):
        recipe = RECIPES[ri]
        if not built[ri]:
            print(f"  {pos + 1}. {recipe}: never needed")
            continue
        clauses = " OR ".join(
            format_combinator_part(c, recipe.in_.txt()) for c in sorted(built[ri])
        )
        print(f"  {pos + 1}. {recipe} [needs {recipe.in_.txt()}]: {clauses}")
    return best_order, built, chance_ready_clauses


def format_combinator_part(c: str, req: str):
    if not len(c):
        return "(always)"

    counts = Counter(c)
    for ch in req:
        if ch in c:
            counts[ch] += 1
    return f"({' AND '.join(f'{ch} >= {counts[ch]}' for ch in sorted(counts))})"
