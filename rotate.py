from itertools import combinations_with_replacement
from graphviz import print_strategy, print_graph
from policy import build_options, print_combinators
from simulate import simulate_combinators
from tarjan import tarjan_scc
from mdp import prune_mec, extract_strategy
from recipe import Recipe
from arcoset import ArcoSet
from search import bfs_all_dist_containing_target
from arco_types import Graph, WorldState


def main():
    # state -> next state -> folding path or random output
    graph: Graph = {}

    recipe_chance_1 = Recipe.from_str("LXZ -> PET", 20)
    recipe_chance_2 = Recipe.from_str("LXZ -> POG", 20)
    fold_limit = 500
    extras_count = 3

    recipe_mats = recipe_chance_1.in_
    assert recipe_mats == recipe_chance_2.in_

    # we're looking for cycles in the graph, and cycles we're interested in
    # must include nodes where we have the ingredients for the recipe. so we
    # iterate over all states where the current set is [recipe mats + N extras]
    for extras_c in combinations_with_replacement("LXEPZTGO", extras_count):
        start = recipe_mats.add(ArcoSet.from_str("".join(extras_c)))
        # we're about to run the production recipe, so our current state is "chance"
        chance_state: WorldState = ("chance", start)
        graph[chance_state] = {}

        # since we're at a state where we want to try running a recipe, the
        # first step is to investigate the state that happens when we get
        # either output
        for chance_recipe in (recipe_chance_1, recipe_chance_2):
            label = chance_recipe.out.txt()
            after = chance_recipe.apply(start)
            # once we've run the production recipe, we then need to run a series
            # of folds/inversions to get back into a ready state (except in edge cases
            # where the current state had multiple copies of the recipe mats)
            choice_state: WorldState = ("choice", after)
            # record that choice_state is reachable from here with one of the random paths
            graph[chance_state][choice_state] = label
            if choice_state not in graph:
                # do the search from choice_state to find out how to get back
                # to ready/chance states
                target_paths_from_choice_state = bfs_all_dist_containing_target(
                    after, recipe_mats, fold_limit
                )
                graph[choice_state] = {
                    ("chance", new_state): dist
                    for new_state, dist in target_paths_from_choice_state.items()
                }

    # now trim down the graph to find the strongly-connected components
    # - ie all sets of states where each state is reachable from the others by at least one path
    sccs = [scc for scc in tarjan_scc(graph) if len(scc) > 1]
    # but then we need to trim it down further - since we can't control the outcome
    # of a chance node, we have to find components where all possible chance outcomes loop
    # back into the component. This is called a "end component" (MEC) in a
    # markov decision process (MDP) and prune_mec currently trims down until it finds
    # a maximal end component
    mecs = [mec for scc in sccs for mec in prune_mec(scc, graph)]
    print(f"{len(graph)} nodes, {len(sccs)} SCCs, {len(mecs)} MECs")
    for mec in mecs:
        chance_states = sorted(n[1].txt() for n in mec if n[0] == "chance")
        print(
            f"MEC with {len(chance_states)} cube-ready states, e.g. {chance_states[:5]}"
        )

    print_graph(graph)

    for i, mec in enumerate(mecs):
        # prune the MEC down further to turn it into a "strategy" - where we have
        # one choice per choice node (but still handle all outcomes for chance nodes)
        #
        # heuristic: we generate a bunch of different strategies based on a given starting
        # node (which guarantees that the strategy includes at least one ready/chance state)
        # and then pick the smallest-looking one
        chance_nodes = [n for n in mec if n[0] == "chance"]
        strategies = [extract_strategy(mec, graph, n) for n in chance_nodes]
        print(
            f"{len(strategies)=}, {max(len(s) for s in strategies)=}, {min(len(s) for s in strategies)=}"
        )
        # pick the strategy with the fewest states, with tiebreaks by names of states
        strategy = min(
            strategies,
            key=lambda g: (len(g), min(n[1].txt() for n in g)),
        )
        print_strategy(i, strategy)
        cube_ready = {n[1] for n in strategy if n[0] == "chance"}
        order, built, cube_clauses = print_combinators(
            build_options(strategy), cube_ready
        )
        simulate_combinators(strategy, order, built, cube_clauses)


if __name__ == "__main__":
    main()
