class ZSet:
    def __init__(self) -> None:
        self._scores: dict[str, float] = {}

    def add(self, member: str, score: float) -> bool:
        """Add or update a member. Returns True if member is new, False if updated"""
        is_new = False if member in self._scores else True
        self._scores[member] = score
        return is_new

    def __len__(self) -> int:
        return len(self._scores)
