
class Lists:
    def __init__(self) -> None:
        self.array: dict[str, list] = {}
    
    def __getitem__(self, item: str) -> list:
        if item not in self.array:
            self.array[item] = []
        return self.array[item]

    def __setitem__(self, list_name: str, list_values: list[str]) -> None:
        """Exending the elements to the list"""
        list_ = self.__getitem__(list_name)
        list_ += list_values
    
    def lset(self, list_name: str, list_values: list[str]) -> None:
        """Prepending elements to the list"""
        list_ = self.__getitem__(list_name)
        self.array[list_name] = list_values[::-1] + list_
