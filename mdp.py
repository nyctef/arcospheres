# modelling tesseracts as a Markov Decision Process (MDP)
# we want to try and find a "maximal end component" - a strongly connected subgraph
# where:
# - any time we have a choice (folding/inversion), we can choose to remain within the component
# - any time there's randomness (tesseract produces either output) then both edges remain in the component


from arco_types import Graph, WorldState, PathLabel
from tarjan import tarjan_scc


def _is_choice_edge(e: PathLabel) -> bool:
    return isinstance(e, int)


def _induced(graph: Graph, vertices: set[WorldState]) -> Graph:
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
    # need to remember to re-split SCCs after pruning, since we may have broken them apart
    work = [set(scc)]
    found: list[list[WorldState]] = []
    while work:
        candidate = work.pop()
        if len(candidate) <= 1:
            continue
        pruned = _prune_set(candidate, graph)
        if len(pruned) <= 1:
            continue
        parts = [set(p) for p in tarjan_scc(_induced(graph, pruned)) if len(p) > 1]
        if len(parts) == 1 and parts[0] == pruned:
            found.append(list(pruned))
        else:
            work.extend(parts)
    return found
