# modelling tesseracts as a Markov Decision Process (MDP)
# we want to try and find a "maximal end component" - a strongly connected subgraph
# where:
# - any time we have a choice (folding/inversion), we can choose to remain within the component
# - any time there's randomness (tesseract produces either output) then both edges remain in the component


from collections import deque

from arco_types import Graph, WorldState, PathLabel
from tarjan import tarjan_scc


def _is_choice_edge(e: PathLabel) -> bool:
    return isinstance(e, int)


def _induced(graph: Graph, vertices: set[WorldState]) -> Graph:
    # the "induced subgraph" is the subgraph which only includes the specified vertices
    return {
        v: {w: e for w, e in graph.get(v, {}).items() if w in vertices}
        for v in vertices
    }


def _prune_set(candidate: set[WorldState], graph: Graph) -> set[WorldState]:
    result = set(candidate)
    changed = True
    while changed:
        changed = False
        for v in list(result):
            out = graph.get(v, {})
            edges = set(out.values())
            targets = set(out.keys())

            if edges and all(_is_choice_edge(e) for e in edges):
                # choice: keep if at least one option stays inside
                keep = any(t in result for t in targets)
            elif edges and not any(_is_choice_edge(e) for e in edges):
                # chance: every outcome must stay inside
                keep = targets.issubset(result)
            else:
                assert False, f"Unexpected edge types for vertex {v}: {edges}"

            if not keep:
                result.remove(v)
                changed = True
    return result


def prune_mec(scc: list[WorldState], graph: Graph) -> list[list[WorldState]]:
    work = [set(scc)]
    found: list[list[WorldState]] = []
    while work:
        candidate = work.pop()
        if len(candidate) <= 1:
            continue
        pruned = _prune_set(candidate, graph)
        if len(pruned) <= 1:
            continue
        # need to remember to re-split SCCs after pruning, since we may have broken them apart
        parts = [set(p) for p in tarjan_scc(_induced(graph, pruned)) if len(p) > 1]
        if len(parts) == 1 and parts[0] == pruned:
            found.append(list(pruned))
        else:
            work.extend(parts)
    return found


def extract_strategy(mec: list[WorldState], graph: Graph, start: WorldState) -> Graph:
    # a "strategy" is a non-maximal "end component" of a decision process.
    # in order to simplify future calculations we look for subsets of the MEC
    # that are still valid for chance nodes (ie for each chance node, all probabilistic
    # outcomes remain within the component))
    inside = set(mec)
    strategy: Graph = {}
    queue: deque[WorldState] = deque([start])
    while queue:
        node = queue.popleft()
        if node in strategy:
            continue
        if node[0] == "chance":
            # both paths must remain inside the component
            strategy[node] = dict(graph[node])
        else:
            # for choice nodes, greedily pick a single edge going back into the component
            options = [
                (next, label) for next, label in graph[node].items() if next in inside
            ]

            def edge_cost(o: tuple[WorldState, PathLabel]) -> tuple[bool, int, str]:
                return (
                    # heuristic: prefer
                    # 1. edges already in the strategy (False sorts before True)
                    o[0] not in strategy,
                    # 2. edges with smaller weights (int(o[1]))
                    int(o[1]),
                    # 3. tiebreaker: sort by name of target state
                    o[0][1].txt(),
                )

            best_next, best_label = min(options, key=edge_cost)
            strategy[node] = {best_next: best_label}
        queue.extend(strategy[node])
    return strategy
