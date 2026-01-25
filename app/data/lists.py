
class Lists:
    def __init__(self) -> None:
        self.array: dict[str, list] = {}
    
    def __getitem__(self, item: str) -> list:
        if not self.__contains__(item):
            self.array[item] = []
        return self.array[item]

    def __setitem__(self, item: str, values: list[str]) -> None:
        """Exending the elements to the list"""
        list_ = self.__getitem__(item)
        list_ += values

    def __contains__(self, item: str):
        return item in self.array
    
    def lset(self, item: str, values: list[str]) -> None:
        """Prepending elements to the list"""
        list_ = self.__getitem__(item)
        self.array[item] = values[::-1] + list_
