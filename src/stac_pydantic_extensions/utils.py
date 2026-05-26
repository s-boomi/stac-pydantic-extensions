def validate_percentage(v: float | int | None) -> float | int | None:
    if v is not None and (v < 0 or v > 100):
        raise ValueError(f"{v} must be between 0 and 100")

    return v
