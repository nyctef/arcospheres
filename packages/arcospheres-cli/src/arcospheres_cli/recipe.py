from .arcoset import ArcoSet
from dataclasses import dataclass


@dataclass(frozen=True)
class Recipe:
    in_: ArcoSet
    out: ArcoSet
    time: int
    internal_name: str

    def can_apply(self, available: ArcoSet) -> bool:
        return available.contains(self.in_)

    def apply(self, available: ArcoSet) -> ArcoSet:
        return available.remove(self.in_).add(self.out)

    @classmethod
    def from_str(cls, recipe: str, time: int, internal_name: str) -> "Recipe":
        in_str, out_str = recipe.split("->")
        in_arco = ArcoSet.from_str(in_str.strip())
        out_arco = ArcoSet.from_str(out_str.strip())
        return cls(in_arco, out_arco, time, internal_name)

    def __str__(self) -> str:
        return f"{self.in_.txt()}->{self.out.txt()}"


RECIPES = [
    # folding
    Recipe.from_str("GX -> ZL", 10, "se-arcosphere-fold-b"),
    Recipe.from_str("XZ -> TP", 10, "se-arcosphere-fold-c"),
    Recipe.from_str("ZP -> GE", 10, "se-arcosphere-fold-f"),
    Recipe.from_str("PG -> OX", 10, "se-arcosphere-fold-g"),
    Recipe.from_str("EO -> LG", 10, "se-arcosphere-fold-h"),
    Recipe.from_str("OL -> XT", 10, "se-arcosphere-fold-a"),
    Recipe.from_str("LT -> EZ", 10, "se-arcosphere-fold-d"),
    Recipe.from_str("TE -> PO", 10, "se-arcosphere-fold-e"),
    # inversion
    Recipe.from_str("LXEP -> ZTGO", 100, "se-arcosphere-fold-out"),
    Recipe.from_str("ZTGO -> LXEP", 100, "se-arcosphere-fold-in"),
]


def get_common_input(recipes: list[Recipe]) -> ArcoSet:
    if not recipes:
        raise ValueError("No recipes provided")
    common = recipes[0].in_
    for r in recipes[1:]:
        assert r.in_ == common, f"mismatched recipe inputs"
    return common
