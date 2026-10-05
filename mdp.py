# modelling tesseracts as a Markov Decision Process (MDP)
# we want to try and find a "maximal end component" - a strongly connected subgraph
# where:
# - any time we have a choice (folding/inversion), we can choose to remain within the component
# - any time there's randomness (tesseract produces either output) then both edges remain in the component


from typing import TypeVar

V = TypeVar("V")
E = TypeVar("E")
Graph = dict[V, dict[V, E]]


def prune_mec(scc: list[V], graph: Graph[V, E]) -> list[V]:
    result = set(scc)
    while True:
        has_changed = False
        if len(result) <= 1:
            return []
        for v in list(result):
            # what kind of outgoing edges does v have?
            # - deterministic > is there a choice to stay in the component? if so keep
            # - nondeterministic > do both choices stay in the compoment? if so keep
            edges = set(graph[v].values())
            targets = set(graph[v].keys())

            # todo: either inject this or admit we're not actually generic on graph types
            choice_edges = [e for e in edges if str(e).isdigit() and int(str(e)) > 0]

            if any(choice_edges):
                # do we have a choice
                if not any(target in result for target in targets):
                    result.remove(v)
                    has_changed = True
                    break

            elif "PET" in edges or "POG" in edges:
                # is nondeterministic
                if not targets.issubset(result):
                    result.remove(v)
                    has_changed = True
                    break
            else:
                assert False, f"Unexpected edge types for vertex {v}: {edges}"

        if not has_changed:
            break
    return list(result)
