from dataclasses import dataclass

_CHARS = "LXEPZTGO"


@dataclass(frozen=True, order=True)
class ArcoSet:
    _arr: tuple[int, ...]

    @classmethod
    def from_str(cls, s: str) -> "ArcoSet":
        assert all(c in _CHARS for c in s), f"Invalid ArcoSet string: {s}"
        arr = tuple(s.count(c) for c in _CHARS)
        return cls(arr)

    @classmethod
    def _from_arcs(cls, arcs: dict[str, int]) -> "ArcoSet":
        assert all(c in _CHARS for c in arcs.keys()), f"Invalid ArcoSet arcs: {arcs}"
        chars: list[str] = []
        for char, count in arcs.items():
            for _ in range(count):
                chars.append(char)
        arr = tuple(arcs.get(c, 0) for c in _CHARS)
        return cls(arr)

    def contains(self, req: "ArcoSet") -> bool:
        for i, req_count in enumerate(req._arr):
            if self._arr[i] < req_count:
                return False
        return True

    def remove(self, req: "ArcoSet") -> "ArcoSet":
        if not self.contains(req):
            raise ValueError("insufficient contents")
        new_arr = tuple(s - r for s, r in zip(self._arr, req._arr))
        return ArcoSet(new_arr)

    def add(self, other: "ArcoSet") -> "ArcoSet":
        new_arr = tuple(s + r for s, r in zip(self._arr, other._arr))
        return ArcoSet(new_arr)

    def as_dict(self) -> dict[str, int]:
        return {c: self._arr[i] for i, c in enumerate(_CHARS)}

    def txt(self) -> str:
        return "".join(c * self._arr[i] for i, c in enumerate(_CHARS))

    def __repr__(self) -> str:
        txt = self.txt()
        return f'ArcoSet.from_str("{txt}")'

    def __str__(self) -> str:
        txt = self.txt()
        return f"AS({txt})"


def format_path(path: list[ArcoSet]) -> str:
    return " -> ".join(str(p.txt()) for p in path)
