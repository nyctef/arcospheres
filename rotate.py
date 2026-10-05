from collections import Counter, defaultdict, deque
from itertools import combinations, combinations_with_replacement
from pathlib import Path
from typing import Callable
from tarjan import tarjan_scc
from mdp import prune_mec
from recipe import Recipe, RECIPES
from arcoset import ArcoSet
from search import bfs_all_dist_containing_target, bfs_one_path_to_exact

PathCache = dict[tuple[ArcoSet, ArcoSet], tuple[int, list[ArcoSet]] | None]


# Nodes are either ("chance", state) (a state with LXZ about to go in the tesseract)
# or ("choice", state)
Node = tuple[str, ArcoSet]
Graph = dict[Node, dict[Node, str]]


def extract_strategy(mec: list[Node], graph: Graph, start: Node) -> Graph:
    inside = set(mec)
    strategy: Graph = {}
    queue: deque[Node] = deque([start])
    while queue:
        node = queue.popleft()
        if node in strategy:
            continue
        if node[0] == "chance":
            strategy[node] = dict(graph[node])
        else:
            options = [(t, l) for t, l in graph[node].items() if t in inside]
            best_t, best_l = min(
                options, key=lambda o: (o[0] not in strategy, int(o[1]), o[0][1].txt())
            )
            strategy[node] = {best_t: best_l}
        queue.extend(strategy[node])
    return strategy


def build_policy(strategy: Graph) -> dict[ArcoSet, Recipe]:
    targets = {n[1] for n in strategy if n[0] == "chance"}
    starts = [n[1] for n in strategy if n[0] == "choice"]

    succ: dict[ArcoSet, list[tuple[Recipe, ArcoSet]]] = {}
    seen = set(starts)
    stack = list(starts)
    while stack:
        state = stack.pop()
        succ[state] = []
        if state in targets:
            continue
        for recipe in RECIPES:
            if recipe.can_apply(state):
                nxt = recipe.apply(state)
                succ[state].append((recipe, nxt))
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)

    preds: dict[ArcoSet, list[ArcoSet]] = defaultdict(list)
    for state, outs in succ.items():
        for _, nxt in outs:
            preds[nxt].append(state)
    dist = {t: 0 for t in targets if t in seen}
    queue: deque[ArcoSet] = deque(dist)
    while queue:
        state = queue.popleft()
        for pred in preds[state]:
            if pred not in dist:
                dist[pred] = dist[state] + 1
                queue.append(pred)

    policy: dict[ArcoSet, Recipe] = {}
    pending = list(starts)
    while pending:
        state = pending.pop()
        if state in targets or state in policy:
            continue
        recipe, nxt = next(o for o in succ[state] if dist.get(o[1]) == dist[state] - 1)
        policy[state] = recipe
        pending.append(nxt)
    return policy


def build_options(strategy: Graph) -> dict[ArcoSet, list[Recipe]]:
    # for every state we might pass through on the way to a cube-ready state, all the
    # recipes that make progress (get one step closer to the nearest cube-ready state)
    targets = {n[1] for n in strategy if n[0] == "chance"}
    starts = [n[1] for n in strategy if n[0] == "choice"]

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

    options: dict[ArcoSet, list[Recipe]] = {}
    pending = list(starts)
    while pending:
        state = pending.pop()
        if state in targets or state in options:
            continue
        options[state] = [r for r, n in succ[state] if dist.get(n) == dist[state] - 1]
        pending.extend(n for _, n in succ[state] if dist.get(n) == dist[state] - 1)
    return options


def learn_decision_list(
    options: dict[ArcoSet, list[Recipe]], size_penalty: float
) -> list[tuple[Recipe, ArcoSet, int]]:
    uncovered = set(options)
    rules: list[tuple[Recipe, ArcoSet, int]] = []
    while uncovered:
        candidates: set[tuple[int, str]] = set()
        for st in uncovered:
            for ri, recipe in enumerate(RECIPES):
                if recipe in options[st]:
                    extras_txt = st.remove(recipe.in_).txt()
                    for size in range(len(extras_txt) + 1):
                        candidates.update(
                            (ri, "".join(c)) for c in combinations(extras_txt, size)
                        )
        best = None
        for ri, extras_txt in candidates:
            recipe = RECIPES[ri]
            pattern = recipe.in_.add(ArcoSet.from_str(extras_txt))
            hit = [st for st in uncovered if st.contains(pattern)]
            if not all(recipe in options[st] for st in hit):
                continue
            key = (
                -len(hit) / (1 + size_penalty * len(extras_txt)),
                len(extras_txt),
                ri,
                extras_txt,
            )
            if best is None or key < best[0]:
                best = (key, recipe, ArcoSet.from_str(extras_txt), hit)
        assert best is not None
        _, recipe, extras, hit = best
        rules.append((recipe, extras, len(hit)))
        uncovered.difference_update(hit)
    return rules


def print_decision_list(options: dict[ArcoSet, list[Recipe]]) -> None:
    # try a few ways of trading rule count against rule size and keep the shortest
    results = [(learn_decision_list(options, p), p) for p in (0.0, 0.25, 0.5, 1.0, 2.0)]
    rules, penalty = min(
        results, key=lambda r: (len(r[0]), sum(len(e.txt()) for _, e, _ in r[0]))
    )
    print(
        f"\nDecision list ({len(rules)} rules covering {len(options)} states, "
        f"size_penalty={penalty}; first match wins):"
    )
    for i, (recipe, extras, n) in enumerate(rules):
        extra_txt = f" + extras {extras.txt()}" if extras.txt() else ""
        print(
            f"  {i + 1:2}. if has {recipe.in_.txt()}{extra_txt}: {recipe}  ({n} states)"
        )


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


CUBE_INPUT = ArcoSet.from_str("LXZ")


def build_cube_policy(
    options: dict[ArcoSet, list[Recipe]], cube_ready: set[ArcoSet]
) -> list[str]:
    forbidden = [
        st for st in options if st.contains(CUBE_INPUT) and st not in cube_ready
    ]
    texts: set[str] = set()
    for st in cube_ready:
        extras_txt = st.remove(CUBE_INPUT).txt()
        for size in range(len(extras_txt) + 1):
            texts.update("".join(c) for c in combinations(extras_txt, size))

    def matches(st: ArcoSet, txt: str) -> bool:
        return st.contains(CUBE_INPUT.add(ArcoSet.from_str(txt)))

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
    options: dict[ArcoSet, list[Recipe]],
    cube_ready: set[ArcoSet],
) -> tuple[list[int], list[list[str]], list[str]]:
    import random

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
    cube_clauses = build_cube_policy(options, cube_ready)
    print(
        f"\nPriority order with {best_cost[0]} clauses total, "
        f"{best_cost[1]} extra-sphere literals ({len(states)} states), "
        f"plus {len(cube_clauses)} clauses for when to cube:"
    )
    cube_text = " OR ".join(
        format_combinator_part(c, CUBE_INPUT.txt()) for c in sorted(cube_clauses)
    )
    print(f"  0. CUBE LXZ [needs LXZ]: {cube_text}")
    for pos, ri in enumerate(best_order):
        recipe = RECIPES[ri]
        if not built[ri]:
            print(f"  {pos + 1}. {recipe}: never needed")
            continue
        clauses = " OR ".join(
            format_combinator_part(c, recipe.in_.txt()) for c in sorted(built[ri])
        )
        print(f"  {pos + 1}. {recipe} [needs {recipe.in_.txt()}]: {clauses}")
    return best_order, built, cube_clauses


def format_combinator_part(c: str, req: str):
    if not len(c):
        return "(always)"

    counts = Counter(c)
    for ch in req:
        if ch in c:
            counts[ch] += 1
    return f"({' AND '.join(f'{ch} >= {counts[ch]}' for ch in sorted(counts))})"


def simulate_combinators(
    strategy: Graph,
    order: list[int],
    built: list[list[str]],
    cube_clauses: list[str],
) -> None:
    cube_ready = {n[1] for n in strategy if n[0] == "chance"}
    cubes = [Recipe.from_str("LXZ -> PET"), Recipe.from_str("LXZ -> POG")]
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


def print_policy(policy: dict[ArcoSet, Recipe]) -> None:
    by_recipe: dict[str, tuple[Recipe, list[ArcoSet]]] = {}
    for state, recipe in policy.items():
        by_recipe.setdefault(str(recipe), (recipe, []))[1].append(state)

    for name, (recipe, states) in sorted(by_recipe.items()):
        print(f"\n{name}: {len(states)} states")
        print("  " + " ".join(sorted(st.txt() for st in states)))

        def matches(st: ArcoSet, extras: ArcoSet) -> bool:
            return st.contains(recipe.in_.add(extras))

        candidates: set[str] = set()
        for st in states:
            extras_txt = st.remove(recipe.in_).txt()
            for size in range(len(extras_txt) + 1):
                candidates.update("".join(c) for c in combinations(extras_txt, size))
        valid = [
            ArcoSet.from_str(c)
            for c in candidates
            if all(
                str(policy[st]) == name
                for st in policy
                if matches(st, ArcoSet.from_str(c))
            )
        ]

        uncovered = set(states)
        rules: list[str] = []
        while uncovered:
            best = min(
                valid,
                key=lambda e: (
                    -sum(1 for st in uncovered if matches(st, e)),
                    len(e.txt()),
                    e.txt(),
                ),
            )
            covered = {st for st in uncovered if matches(st, best)}
            rules.append(f"+{best.txt() or '(nothing)'} ({len(covered)} new)")
            uncovered -= covered
        print(f"  {name} when extras include: " + ", ".join(rules))


def print_graph(graph: Graph, filename: str = "graph_output.txt"):
    out_file = Path(__file__).parent / "scratch" / filename
    out_file.parent.mkdir(exist_ok=True)

    def name(n: Node) -> str:
        return f"{n[0][0]}:{n[1].txt()}"

    with out_file.open("w") as f:
        f.write("digraph G {\n")
        f.write('graph [overlap=scale, sep="+0.5"]; edge [len=1.0];\n')
        for start, edges in graph.items():
            for end, label in edges.items():
                f.write(f'    "{name(start)}" -> "{name(end)}" [label="{label}"];\n')
        f.write("}\n")


def main():
    # source -> target -> path length
    graph: Graph = {}

    cube1 = Recipe.from_str("LXZ -> PET")
    cube2 = Recipe.from_str("LXZ -> POG")
    target = ArcoSet.from_str("LXZ")
    fold_limit = 30
    extras_count = 3
    choice_cache: dict[ArcoSet, dict[ArcoSet, int]] = {}

    for extras_c in combinations_with_replacement("LXEPZTGO", extras_count):
        extras_str = "".join(extras_c)
        start = ArcoSet.from_str("LXZ" + extras_str)
        chance: Node = ("chance", start)
        graph[chance] = {}

        for label, cube in (("PET", cube1), ("POG", cube2)):
            after = cube.apply(start)
            choice: Node = ("choice", after)
            graph[chance][choice] = label
            if choice not in graph:
                if after not in choice_cache:
                    choice_cache[after] = bfs_all_dist_containing_target(
                        after, target, fold_limit
                    )
                graph[choice] = {
                    ("chance", s): str(d) for s, d in choice_cache[after].items()
                }

    sccs = [scc for scc in tarjan_scc(graph) if len(scc) > 1]
    mecs = [mec for scc in sccs for mec in prune_mec(scc, graph)]
    print(f"{len(graph)} nodes, {len(sccs)} SCCs, {len(mecs)} MECs")
    for mec in mecs:
        chance_states = sorted(n[1].txt() for n in mec if n[0] == "chance")
        print(
            f"MEC with {len(chance_states)} cube-ready states, e.g. {chance_states[:5]}"
        )

    print_graph(graph)

    for i, mec in enumerate(mecs):
        chance_nodes = [n for n in mec if n[0] == "chance"]
        strategy = min(
            (extract_strategy(mec, graph, n) for n in chance_nodes),
            key=lambda g: (len(g), min(n[1].txt() for n in g)),
        )
        # relabel choice edges with the actual folds
        labelled: Graph = {}
        print(f"\nStrategy {i}: {len(strategy)} nodes")
        for node, edges in strategy.items():
            labelled[node] = {}
            for target_node, label in edges.items():
                if node[0] == "choice":
                    folds = bfs_one_path_to_exact(node[1], target_node[1])
                    label = ", ".join(str(f) for f in folds) or "(none)"
                labelled[node][target_node] = label
                print(
                    f"  {node[0]}:{node[1].txt()} --[{label}]--> {target_node[0]}:{target_node[1].txt()}"
                )
        print_graph(labelled, f"strategy_{i}.dot")
        cube_ready = {n[1] for n in strategy if n[0] == "chance"}
        order, built, cube_clauses = print_combinators(
            build_options(strategy), cube_ready
        )
        simulate_combinators(strategy, order, built, cube_clauses)


if __name__ == "__main__":
    main()
