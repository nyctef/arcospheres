from collections import defaultdict


class ArcoSet:
    def __init__(self, arcs: dict[str, int]):
        self._arcs = arcs

    @classmethod
    def from_str(cls, s: str) -> "ArcoSet":
        arcs: dict[str, int] = defaultdict(int)
        for char in s:
            arcs[char] += 1
        return cls(arcs)

    def contains(self, req: "ArcoSet") -> bool:
        for char, count in req._arcs.items():
            if self._arcs.get(char, 0) < count:
                return False
        return True

    def remove(self, req: "ArcoSet") -> "ArcoSet":
        if not self.contains(req):
            raise ValueError("insufficient contents")
        new_arcs = self._arcs.copy()
        for char, count in req._arcs.items():
            new_arcs[char] -= count
            if new_arcs[char] == 0:
                del new_arcs[char]
        return ArcoSet(new_arcs)

    def add(self, other: "ArcoSet") -> "ArcoSet":
        new_arcs = self._arcs.copy()
        for char, count in other._arcs.items():
            new_arcs[char] = new_arcs.get(char, 0) + count
        return ArcoSet(new_arcs)

    def __txt(self) -> str:
        strs: list[str] = []
        for char, count in self._arcs.items():
            strs.append(char * count)
        return "".join(strs)

    def __repr__(self) -> str:
        txt = self.__txt()
        return f'ArcoSet.from_str("{txt}")'

    def __str__(self) -> str:
        txt = self.__txt()
        return f"AS({txt})"


class Recipe:
    def __init__(self, in_: ArcoSet, out: ArcoSet):
        self._in = in_
        self._out = out

    def can_apply(self, available: ArcoSet) -> bool:
        return available.contains(self._in)

    def apply(self, available: ArcoSet) -> ArcoSet:
        return available.remove(self._in).add(self._out)

    @classmethod
    def from_str(cls, recipe: str) -> "Recipe":
        in_str, out_str = recipe.split("->")
        in_arco = ArcoSet.from_str(in_str.strip())
        out_arco = ArcoSet.from_str(out_str.strip())
        return cls(in_arco, out_arco)


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


def test_start(start: ArcoSet, target: ArcoSet):
    print()
    print()
    print(f"Starting test with start: {start} and target: {target}")
    start_state = (start, 0)
    stack: list[tuple[ArcoSet, int]] = [start_state]
    seen: set[ArcoSet] = set()

    while stack:
        current, steps = stack.pop()
        if steps > 10:
            print(f"XXXXX Exceeded 10 steps at state: {current}")
            return
        print(current, steps)
        if current.contains(target):
            print(f">>>>> Reached target in {steps} steps")
            return
        for recipe in RECIPES:
            if recipe.can_apply(current):
                next_state = (recipe.apply(current), steps + 1)
                if next_state[0] not in seen:
                    seen.add(next_state[0])
                    stack.append(next_state)
    print(f"XXXXX Failed to reach target from start: {start}")


def main():
    start = ArcoSet.from_str("TEP")
    target = ArcoSet.from_str("LXZ")

    for extra in "LXEPZTGO":
        s = start.add(ArcoSet.from_str(extra))
        test_start(s, target)


if __name__ == "__main__":
    main()
