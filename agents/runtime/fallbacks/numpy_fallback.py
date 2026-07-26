import math
from typing import Any, List, Union

class ndarray:
    """A standard numpy-like ndarray polyfill."""
    def __init__(self, data: List[Any]):
        self.tolist_data = data

    def tolist(self) -> List[Any]:
        """Returns the underlying python list."""
        return self.tolist_data

    def __repr__(self) -> str:
        return f"array({repr(self.tolist_data)})"


def array(data: List[Any]) -> ndarray:
    """Creates a mock ndarray from list data."""
    return ndarray(data)


def mean(data: Union[ndarray, List[Any]], axis: int = None) -> float:
    """Computes the mean reduction of flattening elements."""
    flat = _flatten(data)
    return sum(flat) / len(flat) if flat else 0.0


def sum(data: Union[ndarray, List[Any]], axis: int = None) -> float:
    """Computes the sum of elements."""
    flat = _flatten(data)
    return __builtins__['sum'](flat)


def std(data: Union[ndarray, List[Any]], axis: int = None) -> float:
    """Computes the standard deviation of elements."""
    flat = _flatten(data)
    if not flat:
        return 0.0
    m = mean(flat)
    var = __builtins__['sum']((x - m) ** 2 for x in flat) / len(flat)
    return math.sqrt(var)


def zeros(shape: Union[int, tuple]) -> ndarray:
    """Generates an array filled with zeros."""
    if isinstance(shape, int):
        return ndarray([0.0] * shape)
    # Assume 2D tuple (rows, cols)
    r, c = shape
    return ndarray([[0.0] * c for _ in range(r)])


def ones(shape: Union[int, tuple]) -> ndarray:
    """Generates an array filled with ones."""
    if isinstance(shape, int):
        return ndarray([1.0] * shape)
    r, c = shape
    return ndarray([[1.0] * c for _ in range(r)])


def _flatten(data: Any) -> List[float]:
    """Helper to flatten nested list structure recursively."""
    if isinstance(data, ndarray):
        data = data.tolist_data
    if not isinstance(data, list):
        return [float(data)]
    flat = []
    for item in data:
        if isinstance(item, list):
            flat.extend(_flatten(item))
        else:
            flat.append(float(item))
    return flat
