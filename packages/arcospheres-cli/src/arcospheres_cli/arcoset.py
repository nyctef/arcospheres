from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ArcoSet:
    _txt: str

    @classmethod
    def from_str(cls, s: str) -> "ArcoSet":
        canonical = "".join(sorted(s))
        return cls(canonical)

    @classmethod
    def _from_arcs(cls, arcs: dict[str, int]) -> "ArcoSet":
        chars: list[str] = []
        for char, count in arcs.items():
            for _ in range(count):
                chars.append(char)
        canonical = "".join(sorted(chars))
        return cls(canonical)

    def contains(self, req: "ArcoSet") -> bool:
        for char, count in req._arcs().items():
            if self._arcs().get(char, 0) < count:
                return False
        return True

    def remove(self, req: "ArcoSet") -> "ArcoSet":
        if not self.contains(req):
            raise ValueError("insufficient contents")
        new_arcs = self._arcs().copy()
        for char, count in req._arcs().items():
            new_arcs[char] -= count
            if new_arcs[char] == 0:
                del new_arcs[char]
        return self._from_arcs(new_arcs)

    def add(self, other: "ArcoSet") -> "ArcoSet":
        new_arcs = self._arcs().copy()
        for char, count in other._arcs().items():
            new_arcs[char] = new_arcs.get(char, 0) + count
        return self._from_arcs(new_arcs)

    def _arcs(self) -> dict[str, int]:
        return Counter(self._txt)

    def txt(self) -> str:
        return self._txt

    def __repr__(self) -> str:
        txt = self.txt()
        return f'ArcoSet.from_str("{txt}")'

    def __str__(self) -> str:
        txt = self.txt()
        return f"AS({txt})"


def format_path(path: list[ArcoSet]) -> str:
    return " -> ".join(str(p.txt()) for p in path)
