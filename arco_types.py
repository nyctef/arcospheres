from typing import Literal, Union
from arcoset import ArcoSet

# chance -> next move is probabilistic/adversarial
#           (ie one of the production recipes with randomized outputs)
# choice -> we can choose the next move
#           (ie a folding or inversion recipe)
StateType = Literal["chance", "choice"]
WorldState = tuple[StateType, ArcoSet]
# paths between states are labelled with str in probabilistic cases
# - if we get that output then we move to the next state
# paths are lablelled with int when there's a specific sequence of
# folds/inversions to get to the next state
PathLabel = Union[str, int]
Graph = dict[WorldState, dict[WorldState, PathLabel]]
