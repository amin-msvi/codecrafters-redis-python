def parse_args(pairs: list[str]) -> dict[str, str]:
    pair_map = {}
    for i in range(0, len(pairs), 2):
        pair_map[pairs[i]] = pairs[i + 1]
    return pair_map
