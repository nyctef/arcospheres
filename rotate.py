from collections import defaultdict, deque
from itertools import combinations_with_replacement
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


# Nodes are either ("chance", state) - a state with LXZ about to go in the tesseract -
# or ("choice", state) - a state just after the tesseract, where we choose how to fold.
Node = tuple[str, ArcoSet]
Graph = dict[Node, dict[Node, str]]


def print_graph(graph: Graph):
    out_file = Path(__file__).parent / "scratch" / "graph_output.txt"
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


if __name__ == "__main__":
    main()
