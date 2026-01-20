# class DataStoreKeyError(Exception):
#     def __init__(self, key, value=None):
#         self.key = key

#         message = f"key {key} not found."

#         super().__init__(message)


class DataStore:
    def __init__(self):
        self.data = {}

    def set(self, key, val):
        self.data.update({key: val})

    def get(self, key):
        return self.data.get(
            key,
        )
