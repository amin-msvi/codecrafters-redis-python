from random import randint
from typing import Any

KeyValuePair = dict[str, Any]


class Stream:
    def __init__(self) -> None:
        self.streams: dict[str, KeyValuePair] = {}

    def __getitem__(self, stream_key: str) -> KeyValuePair | None:
        return self.streams.get(stream_key)

    def __setitem__(self, stream_info: tuple[str, str | None], pairs: KeyValuePair) -> None:
        stream: KeyValuePair = self.streams.get(stream_info[0], {})
        stream_id = stream_info[1] if stream_info[1] is not None else self._generate_id()
        stream.update({stream_id: pairs})

    def _generate_id(self) -> str:
        return str(randint(1, 100))
