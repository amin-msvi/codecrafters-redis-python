def get_expiry(args: list) -> float | None:
    for arg_idx in range(len(args)):
        if isinstance(args[arg_idx], str):
            if args[arg_idx].upper() == "PX":
                return float(args[arg_idx+1]) if arg_idx + 1 <= len(args) else None
            if args[arg_idx].upper() == "EX":
                return float(args[arg_idx+1]) * 1000 if arg_idx + 1 < len(args) else None
    return None
