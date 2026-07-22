from enum import Enum
from typing import Any, Literal

def enum_to_values(enums: type[Enum], as_literal: bool = False) -> list[str] | Any:
    values = [item.value for item in enums]

    if as_literal:
        return Literal[*values]

    return values