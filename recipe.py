from arcoset import ArcoSet
from dataclasses import dataclass


@dataclass
class Recipe:
    in_: ArcoSet
    out: ArcoSet

    def can_apply(self, available: ArcoSet) -> bool:
        return available.contains(self.in_)

    def apply(self, available: ArcoSet) -> ArcoSet:
        return available.remove(self.in_).add(self.out)

    @classmethod
    def from_str(cls, recipe: str) -> "Recipe":
        in_str, out_str = recipe.split("->")
        in_arco = ArcoSet.from_str(in_str.strip())
        out_arco = ArcoSet.from_str(out_str.strip())
        return cls(in_arco, out_arco)

    def __str__(self) -> str:
        return f"{self.in_.txt()}->{self.out.txt()}"


RECIPES = [
    # folding
    Recipe.from_str("XG -> ZL"),
    Recipe.from_str("XZ -> PT"),
    Recipe.from_str("ZP -> GE"),
    Recipe.from_str("GP -> XO"),
    Recipe.from_str("OE -> LG"),
    Recipe.from_str("OL -> TX"),
    Recipe.from_str("TL -> EZ"),
    Recipe.from_str("TE -> OP"),
    # inversion
    Recipe.from_str("LXEP -> ZTGO"),
    Recipe.from_str("ZTGO -> LXEP"),
]
