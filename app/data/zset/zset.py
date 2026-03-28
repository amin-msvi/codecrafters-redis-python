class ZSet:
    def __init__(self) -> None:
        self._scores: dict[str, float] = {}

    def add(self, member: str, score: float) -> bool:
        """Add or update a member. Returns True if member is new, False if updated"""
        is_new = False if member in self._scores else True
        self._scores[member] = score
        return is_new

    def rank(self, member: str) -> int | None:
        """Return 0-based rank by ascending score, or None if not found"""
        # It's a dummy solution for now. I'll get back to this. Do the following:
        # 1. Design a better solution to save the items sorted in the first place
        # 2. Just check the index for the rank
        if member not in self._scores:
            return None
        
        sorted_list = sorted(self._scores.items(), key=lambda x: (x[1], x[0]))
        for i, (name, _) in enumerate(sorted_list):
            if name == member:
                return i

    def range_by_rank(self, start: int, stop: int) -> list[str]:
        """Return members in [start, stop] rank range (inclusive), ascending order."""
        sorted_members = sorted(self._scores.items(), key=lambda x: (x[1], x[0]))
        members = [entry[0] for entry in sorted_members[start : stop+1]]
        return members

    def __len__(self) -> int:
        return len(self._scores)
