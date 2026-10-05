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

    def txt(self) -> str:
        strs: list[str] = []
        for char, count in self._arcs.items():
            for _ in range(count):
                strs.append(char)
        strs.sort()
        return "".join(strs)

    def __repr__(self) -> str:
        txt = self.txt()
        return f'ArcoSet.from_str("{txt}")'

    def __str__(self) -> str:
        txt = self.txt()
        return f"AS({txt})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArcoSet):
            return False
        return self._arcs == other._arcs

    def __hash__(self) -> int:
        return hash(frozenset(self._arcs.items()))


def format_path(path: list[ArcoSet]) -> str:
    return " -> ".join(str(p.txt()) for p in path)
