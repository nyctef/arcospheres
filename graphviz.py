from pathlib import Path
from arco_types import Graph, WorldState
from search import bfs_one_path_to_exact


def print_graph(graph: Graph, filename: str = "graph_output.txt"):
    out_file = Path(__file__).parent / "scratch" / filename
    out_file.parent.mkdir(exist_ok=True)

    def name(n: WorldState) -> str:
        return f"{n[0][0]}:{n[1].txt()}"

    with out_file.open("w") as f:
        f.write("digraph G {\n")
        f.write('graph [overlap=scale, sep="+0.5"]; edge [len=1.0];\n')
        for start, edges in graph.items():
            for end, label in edges.items():
                f.write(f'    "{name(start)}" -> "{name(end)}" [label="{label}"];\n')
        f.write("}\n")


def print_strategy(i: int, strategy: Graph):
    # relabel choice edges with the actual folds
    labelled: Graph = {}
    print(f"\nStrategy {i}: {len(strategy)} nodes")
    for node, edges in strategy.items():
        labelled[node] = {}
        for target_node, label in edges.items():
            if node[0] == "choice":
                # unfortunately we lost the fold path info, so reconstruct it
                folds = bfs_one_path_to_exact(node[1], target_node[1])
                label = ", ".join(str(f) for f in folds) or "(none)"
            labelled[node][target_node] = label
            print(
                f"  {node[0]}:{node[1].txt()} --[{label}]--> {target_node[0]}:{target_node[1].txt()}"
            )
    print_graph(labelled, f"strategy_{i}.dot")
