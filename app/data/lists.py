
class Lists:
    def __init__(self) -> None:
        self.array: dict[str, list] = {}
    
    def __getitem__(self, item: str) -> list:
        if item not in self.array:
            self.array[item] = []
        return self.array[item]

    def __setitem__(self, list_name, list_values) -> None:
        list_ = self.__getitem__(list_name)
        list_ += list_values
