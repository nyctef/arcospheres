from typing import TypeVar

V = TypeVar("V")
E = TypeVar("E")
Graph = dict[V, dict[V, E]]


def tarjan_scc(graph: Graph[V, E]):
    index_counter = 0
    index: dict[V, int] = {}
    lowlink: dict[V, int] = {}
    on_stack: set[V] = set()
    stack: list[V] = []
    sccs: list[list[V]] = []

    def strongconnect(v: V):
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
            component: list[V] = []
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
