class ZSet:
    def __init__(self) -> None:
        self._entries: list[tuple] = []
    
    def add(self, entry):
        self._entries.append(entry)  # For now, I'm just appending at the end without considering the score

    def __len__(self) -> int:
        return len(self._entries)
