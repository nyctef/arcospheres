from arcoset import ArcoSet
from collections import deque
from recipe import Recipe, RECIPES


def bfs_all_dist_containing_target(
    current: ArcoSet, target: ArcoSet, limit: int
) -> dict[ArcoSet, int]:
    """all distances to states that are a superset of `target`, within `limit`"""
    if current.contains(target):
        return {}
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


def bfs_one_path_to_exact(start: ArcoSet, goal: ArcoSet) -> list[Recipe]:
    """single shortest path to state that exactly matches `goal`"""
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
