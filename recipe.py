from arcoset import ArcoSet
from dataclasses import dataclass


@dataclass
class Recipe:
    in_: ArcoSet
    out: ArcoSet
    time: int

    def can_apply(self, available: ArcoSet) -> bool:
        return available.contains(self.in_)

    def apply(self, available: ArcoSet) -> ArcoSet:
        return available.remove(self.in_).add(self.out)

    @classmethod
    def from_str(cls, recipe: str, time: int) -> "Recipe":
        in_str, out_str = recipe.split("->")
        in_arco = ArcoSet.from_str(in_str.strip())
        out_arco = ArcoSet.from_str(out_str.strip())
        return cls(in_arco, out_arco, time)

    def __str__(self) -> str:
        return f"{self.in_.txt()}->{self.out.txt()}"


RECIPES = [
    # folding
    Recipe.from_str("XG -> ZL", 10),
    Recipe.from_str("XZ -> PT", 10),
    Recipe.from_str("ZP -> GE", 10),
    Recipe.from_str("GP -> XO", 10),
    Recipe.from_str("OE -> LG", 10),
    Recipe.from_str("OL -> TX", 10),
    Recipe.from_str("TL -> EZ", 10),
    Recipe.from_str("TE -> OP", 10),
    # inversion
    Recipe.from_str("LXEP -> ZTGO", 100),
    Recipe.from_str("ZTGO -> LXEP", 100),
]
