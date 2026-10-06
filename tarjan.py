from arco_types import Graph, WorldState


def tarjan_scc(graph: Graph):
    index_counter = 0
    index: dict[WorldState, int] = {}
    lowlink: dict[WorldState, int] = {}
    on_stack: set[WorldState] = set()
    stack: list[WorldState] = []
    sccs: list[list[WorldState]] = []

    def strongconnect(v: WorldState):
        nonlocal index_counter
        index[v] = index_counter
        lowlink[v] = index_counter
        index_counter += 1
        stack.append(v)
        on_stack.add(v)

        for w, _ in graph.get(v, {}).items():
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            component: list[WorldState] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                component.append(w)
                if w == v:
                    break
            sccs.append(component)

    for v in graph:
        if v not in index:
            strongconnect(v)

    return sccs
