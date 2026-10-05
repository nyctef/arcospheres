from collections import Counter, defaultdict, deque
from itertools import combinations, combinations_with_replacement
from pathlib import Path
from tarjan import tarjan_scc
from mdp import prune_mec


class ArcoSet:
    def __init__(self, arcs: dict[str, int]):
        self._arcs = arcs

    @classmethod
    def from_str(cls, s: str) -> "ArcoSet":
        arcs: dict[str, int] = defaultdict(int)
        for char in s:
            arcs[char] += 1
        return cls(arcs)

    def contains(self, req: "ArcoSet") -> bool:
        for char, count in req._arcs.items():
            if self._arcs.get(char, 0) < count:
                return False
        return True

    def remove(self, req: "ArcoSet") -> "ArcoSet":
        if not self.contains(req):
            raise ValueError("insufficient contents")
        new_arcs = self._arcs.copy()
        for char, count in req._arcs.items():
            new_arcs[char] -= count
            if new_arcs[char] == 0:
                del new_arcs[char]
        return ArcoSet(new_arcs)

    def add(self, other: "ArcoSet") -> "ArcoSet":
        new_arcs = self._arcs.copy()
        for char, count in other._arcs.items():
            new_arcs[char] = new_arcs.get(char, 0) + count
        return ArcoSet(new_arcs)

    def txt(self) -> str:
        strs: list[str] = []
        for char, count in self._arcs.items():
            for _ in range(count):
                strs.append(char)
        strs.sort()
        return "".join(strs)

    def __repr__(self) -> str:
        txt = self.txt()
        return f'ArcoSet.from_str("{txt}")'

    def __str__(self) -> str:
        txt = self.txt()
        return f"AS({txt})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArcoSet):
            return False
        return self._arcs == other._arcs

    def __hash__(self) -> int:
        return hash(frozenset(self._arcs.items()))


def format_path(path: list[ArcoSet]) -> str:
    return " -> ".join(str(p.txt()) for p in path)


class Recipe:
    def __init__(self, in_: ArcoSet, out: ArcoSet):
        self._in = in_
        self._out = out

    def can_apply(self, available: ArcoSet) -> bool:
        return available.contains(self._in)

    def apply(self, available: ArcoSet) -> ArcoSet:
        return available.remove(self._in).add(self._out)

    @classmethod
    def from_str(cls, recipe: str) -> "Recipe":
        in_str, out_str = recipe.split("->")
        in_arco = ArcoSet.from_str(in_str.strip())
        out_arco = ArcoSet.from_str(out_str.strip())
        return cls(in_arco, out_arco)

    def __str__(self) -> str:
        return f"{self._in.txt()}->{self._out.txt()}"


RECIPES = [
    # folding
    Recipe.from_str("XG -> ZL"),
    Recipe.from_str("XZ -> PT"),
    Recipe.from_str("ZP -> GE"),
    Recipe.from_str("GP -> XO"),
    Recipe.from_str("OE -> LG"),
    Recipe.from_str("OL -> TX"),
    Recipe.from_str("TL -> EZ"),
    Recipe.from_str("TE -> OP"),
    # inversion
    Recipe.from_str("LXEP -> ZTGO"),
    Recipe.from_str("ZTGO -> LXEP"),
    # tesseract
    # Recipe.from_str("LXZ -> TEP"),
    # Recipe.from_str("LXZ -> GOP"),
]

PathCache = dict[tuple[ArcoSet, ArcoSet], tuple[int, list[ArcoSet]] | None]

log_count = 0
cache_hit_count = 0
cache_add_count = 0

missing = object()


def find_path(
    start: ArcoSet, target: ArcoSet, limit: int, cache: PathCache
) -> tuple[int, list[ArcoSet]] | None:
    # print()
    # print()
    # print(f"Starting test with start: {start} and target: {target}")
    queue: deque[tuple[ArcoSet, int, list[ArcoSet]]] = deque([(start, 0, [])])
    seen: set[ArcoSet] = set()
    global cache_hit_count, cache_add_count

    def log(
        current: ArcoSet, steps: int, path: list[ArcoSet], force: bool = False
    ) -> None:
        global log_count
        global cache_hit_count, cache_add_count
        if force or log_count % 10_000_000 == 0:
            print(
                f"{current=} {steps=} {len(cache)=} {cache_hit_count=} {cache_add_count=} {log_count=} {len(seen)=}"
            )
        log_count += 1

    while queue:
        current, steps, path = queue.popleft()
        log(current, steps, path, force=False)
        if steps > limit:
            # print(f"XXXXX Exceeded {limit} steps at state: {current}")
            continue
        # print(current, steps)

        path_to_current = path + [current]

        # if (
        #     r := cache.get((current, target), missing)
        # ) is not None and r is not missing:
        #     cache_hit_count += 1
        #     (
        #         remaining_count,  # pyright: ignore[reportUnknownVariableType]
        #         remaining_path,  # pyright: ignore[reportUnknownVariableType]
        #     ) = r  # pyright: ignore[reportGeneralTypeIssues, reportUnknownVariableType]
        #     # print(f"{steps=} {remaining_count=} {path=} {remaining_path=}")
        #     return (
        #         steps + remaining_count,
        #         path + remaining_path,
        #     )  # pyright: ignore[reportUnknownVariableType]

        # cache[(start, current)] = (steps, path_to_current)
        # cache_add_count += 1

        if current.contains(target):
            # print(f">>>>> Reached target in {steps} steps")
            return steps, path_to_current
        for recipe in RECIPES:
            if recipe.can_apply(current):
                next_state = (recipe.apply(current), steps + 1, path_to_current)
                if next_state[0] not in seen:
                    seen.add(next_state[0])
                    queue.append(next_state)
    # print(f"XXXXX Failed to reach target from start: {start}")
    # log(start, limit, [], force=True)
    cache[(start, target)] = None
    return None


def find_cycle(start: ArcoSet, limit: int) -> tuple[int, list[ArcoSet]] | None:
    stack: list[tuple[ArcoSet, int, list[ArcoSet]]] = [(start, 0, [])]
    seen: set[ArcoSet] = set()

    while stack:
        current, steps, path = stack.pop()
        if steps > limit:
            continue
        if steps > 0 and current == start:
            return steps, path
        for recipe in RECIPES:
            if recipe.can_apply(current):
                next_state = (recipe.apply(current), steps + 1, path + [current])
                if next_state[0] not in seen:
                    seen.add(next_state[0])
                    stack.append(next_state)
    return None


def find_cycles():
    # start = ArcoSet.from_str("GOP")
    target = ArcoSet.from_str("LXZ")
    limit = 10

    for c in range(3, 10):
        print(f"Checking cycles for count {c} spheres with limit {limit}")
        for start_c in combinations_with_replacement("LXEPZTGO", c):
            start_str = "".join(start_c)
            start = ArcoSet.from_str(start_str)
            cycle = find_cycle(start, limit)
            if cycle is not None:
                cycle_length, path = cycle
                if not any(state.contains(target) for state in path):
                    continue
                print(f"Found cycle of length {cycle_length} for start: {start_str}")
                print("Path:")
                for state in path:
                    print(state)


def find_specific_cycle(input: ArcoSet, output: ArcoSet, limit: int):
    # input = ArcoSet.from_str("G")
    # output = ArcoSet.from_str("O")
    # limit = 10

    shortest_len = 999
    shortest_path: list[ArcoSet] = []

    for extras_count in range(1, 10):
        print(
            f"Checking paths for extras count {extras_count} spheres with limit {limit}"
        )
        cache: PathCache = {}
        for extras_c in combinations_with_replacement("LXEPZTGO", extras_count):
            extras_str = "".join(extras_c)
            extras = ArcoSet.from_str(extras_str)
            start = input.add(extras)
            target = output.add(extras)
            if (p := find_path(start, target, limit, cache)) is not None:
                path_length, path = p
                if path_length < shortest_len:
                    shortest_len = path_length
                    shortest_path = path
                    print()
                    print(
                        f">>>>> Found shorter path for extras: {extras_str} | Path: {format_path(shortest_path)}"
                    )
                    print()


def reachable_with_target(
    current: ArcoSet, target: ArcoSet, limit: int
) -> dict[ArcoSet, int]:
    """All states reachable within `limit` folds that contain `target`,
    mapped to the minimum number of folds needed (0 = already there)."""
    dist: dict[ArcoSet, int] = {current: 0}
    queue: deque[ArcoSet] = deque([current])
    while queue:
        state = queue.popleft()
        steps = dist[state]
        if steps >= limit:
            continue
        for recipe in RECIPES:
            if recipe.can_apply(state):
                nxt = recipe.apply(state)
                if nxt not in dist:
                    dist[nxt] = steps + 1
                    queue.append(nxt)
    return {s: d for s, d in dist.items() if s.contains(target)}


# Nodes are either ("chance", state) (a state with LXZ about to go in the tesseract)
# or ("choice", state)
Node = tuple[str, ArcoSet]
Graph = dict[Node, dict[Node, str]]


def fold_sequence(start: ArcoSet, goal: ArcoSet) -> list[Recipe]:
    parents: dict[ArcoSet, tuple[ArcoSet, Recipe] | None] = {start: None}
    queue: deque[ArcoSet] = deque([start])
    while queue:
        state = queue.popleft()
        if state == goal:
            break
        for recipe in RECIPES:
            if recipe.can_apply(state):
                nxt = recipe.apply(state)
                if nxt not in parents:
                    parents[nxt] = (state, recipe)
                    queue.append(nxt)
    steps: list[Recipe] = []
    node = goal
    while (p := parents[node]) is not None:
        node, recipe = p
        steps.append(recipe)
    steps.reverse()
    return steps


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
        pending.extend(n for r, n in succ[state] if dist.get(n) == dist[state] - 1)
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
                    extras_txt = st.remove(recipe._in).txt()
                    for size in range(len(extras_txt) + 1):
                        candidates.update(
                            (ri, "".join(c)) for c in combinations(extras_txt, size)
                        )
        best = None
        for ri, extras_txt in candidates:
            recipe = RECIPES[ri]
            pattern = recipe._in.add(ArcoSet.from_str(extras_txt))
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
            f"  {i + 1:2}. if has {recipe._in.txt()}{extra_txt}: {recipe}  ({n} states)"
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
        while must:
            best = max(
                valid,
                key=lambda c: (
                    (c[1] & must).bit_count(),
                    (c[1] & unhandled).bit_count(),
                    -len(c[0]),
                ),
            )
            if not (best[1] & must):
                return None
            result[ri].append(best[0])
            unhandled &= ~best[1]
            must &= ~best[1]
    return result if not unhandled else None


def print_combinators(
    options: dict[ArcoSet, list[Recipe]],
) -> tuple[list[int], list[list[str]]]:
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
                extras_txt = st.remove(recipe._in).txt()
                for size in range(len(extras_txt) + 1):
                    texts.update("".join(c) for c in combinations(extras_txt, size))
        for txt in texts:
            pattern = recipe._in.add(ArcoSet.from_str(txt))
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
    print(
        f"\nPriority order with {best_cost[0]} clauses total, "
        f"{best_cost[1]} extra-sphere literals ({len(states)} states):"
    )
    for pos, ri in enumerate(best_order):
        recipe = RECIPES[ri]
        if not built[ri]:
            print(f"  {pos + 1}. {recipe}: never needed")
            continue
        clauses = " OR ".join(
            format_combinator_part(c, recipe._in.txt()) for c in sorted(built[ri])
        )
        print(f"  {pos + 1}. {recipe} [needs {recipe._in.txt()}]: {clauses}")
    return best_order, built


def format_combinator_part(c: str, req: str):
    if not len(c):
        return "(always)"

    counts = Counter(c)
    for ch in req:
        if ch in c:
            counts[ch] += 1
    return f"({' AND '.join(f'{ch} >= {counts[ch]}' for ch in sorted(counts))})"


def simulate_combinators(
    strategy: Graph, order: list[int], built: list[list[str]]
) -> None:
    cube_ready = {n[1] for n in strategy if n[0] == "chance"}
    cubes = [Recipe.from_str("LXZ -> PET"), Recipe.from_str("LXZ -> POG")]
    rules = [
        (RECIPES[ri], [recipe_in_plus(RECIPES[ri], c) for c in built[ri]])
        for ri in order
        if built[ri]
    ]

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
            while state not in cube_ready:
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
        f"all return to a cube-ready state (max {max_folds} folds)"
    )


def recipe_in_plus(recipe: Recipe, extras_txt: str) -> ArcoSet:
    return recipe._in.add(ArcoSet.from_str(extras_txt))


def print_policy(policy: dict[ArcoSet, Recipe]) -> None:
    by_recipe: dict[str, tuple[Recipe, list[ArcoSet]]] = {}
    for state, recipe in policy.items():
        by_recipe.setdefault(str(recipe), (recipe, []))[1].append(state)

    for name, (recipe, states) in sorted(by_recipe.items()):
        print(f"\n{name}: {len(states)} states")
        print("  " + " ".join(sorted(st.txt() for st in states)))

        def matches(st: ArcoSet, extras: ArcoSet) -> bool:
            return st.contains(recipe._in.add(extras))

        candidates: set[str] = set()
        for st in states:
            extras_txt = st.remove(recipe._in).txt()
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
    # find_specific_cycle(
    #     input=ArcoSet.from_str("GOP"),
    #     output=ArcoSet.from_str("LXZ"),
    #     limit=30,
    # )

    # try drawing a graph of all 1-extra and 2-extra paths
    # -> are there loops for PET or POG?
    # -> are there loops that work for both?

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
                    choice_cache[after] = reachable_with_target(
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
                    folds = fold_sequence(node[1], target_node[1])
                    label = ", ".join(str(f) for f in folds) or "(none)"
                labelled[node][target_node] = label
                print(
                    f"  {node[0]}:{node[1].txt()} --[{label}]--> {target_node[0]}:{target_node[1].txt()}"
                )
        print_graph(labelled, f"strategy_{i}.dot")
        order, built = print_combinators(build_options(strategy))
        simulate_combinators(strategy, order, built)


if __name__ == "__main__":
    main()
