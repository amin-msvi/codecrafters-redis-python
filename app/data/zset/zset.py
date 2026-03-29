"""
The underlying data structure for zset is not efficient at all.
Just for the sake of simplicity, I implemented a dummy hashmap-base solution.
At some point, I'll get back to it and I might implement it with hashmap + skip lists (just like the prd redis)
"""


class ZSet:
    def __init__(self) -> None:
        self._scores: dict[str, float] = {}

    def add(self, member: str, score: float) -> bool:
        """Add or update a member. Returns True if member is new, False if updated"""
        is_new = False if member in self._scores else True
        self._scores[member] = score
        return is_new

    def score(self, member: str) -> float | None:
        """Return the score for a member, or None if not found."""
        return self._scores.get(member)

    def rank(self, member: str) -> int | None:
        """Return 0-based rank by ascending score, or None if not found"""
        if member not in self._scores:
            return None

        sorted_list = sorted(self._scores.items(), key=lambda x: (x[1], x[0]))
        for i, (name, _) in enumerate(sorted_list):
            if name == member:
                return i

    def range_by_rank(self, start: int, stop: int) -> list[str]:
        """Return members in [start, stop] rank range (inclusive), ascending order."""
        sorted_members = sorted(self._scores.items(), key=lambda x: (x[1], x[0]))

        # Negative Index
        if start < 0:
            start = max(0, start + len(self))
        if stop < 0:
            stop = max(0, stop + len(self))

        members = [entry[0] for entry in sorted_members[start : stop + 1]]
        return members

    def remove(self, member: str) -> int:
        removed = self._scores.pop(member, None)
        return 1 if removed is not None else 0

    def __len__(self) -> int:
        return len(self._scores)
