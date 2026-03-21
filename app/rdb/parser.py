from app.rdb.types import ParsedRDB, RDBEntry, RDBProtocolError, SpecialStringEncoded


class RDBParser:
    def __init__(self, data: bytes):
        self.data: bytes = data
        self.cursor: int = 0

    def parse(self) -> ParsedRDB:
        version: str = self._parse_header()
        metadata: dict[str, str] = {}
        entries: dict[str, RDBEntry] = {}

        while True:
            byte = self._consume_byte()

            if byte == 0xFA:
                self._parse_metadata(metadata)
            elif byte == 0xFE:
                self._parse_database(entries)
            elif byte == 0xFF:
                break
            else:
                raise RDBProtocolError("RDB protocol error")

        return ParsedRDB(
            version=version,
            metadata=metadata,
            data=entries,
        )

    # Private methods
    def _parse_header(self) -> str:
        chunk = self._consume(9)
        if chunk[:5] != b"REDIS":
            raise RDBProtocolError("Invalid RDB protocol")
        return chunk[5:].decode("utf-8")

    def _parse_metadata(self, metadata: dict[str, str]):
        """
        FA                              ← already consumed by parse() loop
        09 72 65 64 69 73 2D 76 65 72   ← name  (string encoded): "redis-ver"
        06 36 2E 30 2E 31 36            ← value (string encoded): "6.0.16"
        """
        name = self._read_string()
        value = self._read_string()
        metadata.update({name: value})

    def _parse_database(self, entries: dict[str, RDBEntry]):
        """
        FE          ← already consumed by parse() loop
        00          ← database index (size encoded)
        FB          ← marker: hash table sizes follow
        03          ← total keys (size encoded)
        02          ← keys with expiry (size encoded)
        [key-value pairs...]
        """
        # index: We don't need the `index` for this stage, so I'll leave it here
        _ = self._read_size_encoding()
        marker = self._consume_byte()
        if marker != 0xFB:
            raise RDBProtocolError("No marker")
        total_keys = self._read_size_encoding()
        self._read_size_encoding()  # expiry_keys count is here. Not needed for now. Consumed it
        assert isinstance(total_keys, int)
        for _ in range(total_keys):
            key, entry = self._parse_key_value()
            entries[key] = entry

    def _parse_key_value(
        self,
    ) -> tuple[
        str, RDBEntry
    ]:  # Remove None whenever the other types of dtypes are implemented.
        # If there's the optional expiry
        expiry: datetime | None = None
        if self._peek()[0] == 0xFC:
            self._consume_byte()  # Consuming 0xFC
            expiry = datetime.fromtimestamp(int.from_bytes(self._consume(8), "little"))
        elif self._peek()[0] == 0xFD:
            self._consume_byte()  # Consuming 0xFD
            expiry_s = int.from_bytes(self._consume(4), "little")
            expiry = datetime.fromtimestamp(expiry_s * 1000)

        value_byte_type = self._consume_byte()
        if value_byte_type == 0:  # string type (for now we only support this)
            key = self._read_string()
            value = self._read_string()
            return key, RDBEntry(value=value, dtype="string", expiry=expiry)
        else:
            return "not-implemented-yet", RDBEntry(
                value="value", dtype="something else", expiry=expiry
            )

    def _consume(self, n: int) -> bytes:
        chunk = self._peek(n)
        self.cursor += n
        return chunk

    def _consume_byte(self) -> int:
        byte = self.data[self.cursor]
        self.cursor += 1
        return byte

    def _peek(self, n=1) -> bytes:
        return self.data[self.cursor : self.cursor + n]

    def _read_string(self) -> str:
        first_byte = self._peek()[0]
        if (first_byte >> 6) == 0b11:  # SpecialStringEncoded cases
            byte = self._consume_byte()
            bottom_6_bits = byte & 0b00111111
            if bottom_6_bits == 0x00:  # 0b000000
                b = self._consume_byte()  # int8 -> str(value)
                return str(b)
            elif bottom_6_bits == 0x01:  # 0b000001
                b = self._consume(2)  # int16 little-endian -> str(value)
                return str(int.from_bytes(b, "little"))
            elif bottom_6_bits == 0x02:  # 0b000010
                b = self._consume(4)  # int32 little-endian -> str(value)
                return str(int.from_bytes(b, "little"))
            else:
                raise RDBProtocolError("wrong special encoded string format")
        else:
            size = self._read_size_encoding()  # How many bytes follow?
            assert isinstance(size, int)
            raw = self._consume(size)  # reading those bytes
            return raw.decode("utf-8")  # Convert to string

    def _read_size_encoding(self) -> int | SpecialStringEncoded:
        first_byte = self._consume_byte()
        flag = (first_byte & 0b11000000) >> 6

        if flag == 0b00:  # short length -> bottom 6 bits
            return first_byte & 0b00111111

        elif (
            flag == 0b01
        ):  # medium length -> bottom 6 bits + next byte (6+8=14 bits, big endian)
            bottom_bits = first_byte & 0b00111111  # High part
            next_byte = self._consume_byte()  # Low part
            return (bottom_bits << 8) | next_byte

        elif flag == 0b10:  # large length -> next 4 bytes (32 bits, big endian)
            next_4_bytes = self._consume(4)
            merged = 0
            for b in next_4_bytes:
                merged = (merged << 8) | b
            return merged

        elif flag == 0b11:  # special integer encoding
            # This is a 'special string encoding' (integer encoded as string).
            # Sending back signal to the caller -> This is special case
            return SpecialStringEncoded()

        else:
            raise RDBProtocolError("Invalid size encoding protcol")
