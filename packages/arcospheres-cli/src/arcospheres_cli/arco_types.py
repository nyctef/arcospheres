from dataclasses import dataclass
from typing import Literal, Union
from .arcoset import ArcoSet

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


@dataclass(frozen=True)
class CombinatorClause:
    leftsignal: str  # future: expand to union(signal, constant)
    comparison: Literal["="]  # ...
    rightconstant: int

    def __str__(self) -> str:
        return f"{self.leftsignal}{self.comparison}{self.rightconstant}"

    def is_satisfied_by(self, ars: ArcoSet) -> bool:
        return ars.as_dict().get(self.leftsignal, 0) == self.rightconstant


@dataclass(frozen=True)
class And:
    clauses: tuple[CombinatorClause, ...]

    def __str__(self) -> str:
        return " AND ".join(str(c) for c in self.clauses)

    def is_satisfied_by(self, ars: ArcoSet) -> bool:
        return all(c.is_satisfied_by(ars) for c in self.clauses)


@dataclass(frozen=True)
class Or:
    clauses: tuple[And, ...]

    def __str__(self) -> str:
        return " OR ".join(f"({a})" for a in self.clauses)

    def is_satisfied_by(self, ars: ArcoSet) -> bool:
        return any(a.is_satisfied_by(ars) for a in self.clauses)
