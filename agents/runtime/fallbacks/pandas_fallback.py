import csv
from typing import Dict, List, Tuple, Any, Generator, Union

class Series:
    """A standard pandas-like Series polyfill."""
    def __init__(self, data: List[Any], name: str = None):
        self._data = list(data)
        self.name = name

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, idx: int) -> Any:
        return self._data[idx]

    def __iter__(self) -> Generator[Any, None, None]:
        yield from self._data

    # Comparisons for boolean indexing
    def __gt__(self, other: Any) -> 'Series':
        return Series([x > other if x is not None else False for x in self._data], name=self.name)

    def __lt__(self, other: Any) -> 'Series':
        return Series([x < other if x is not None else False for x in self._data], name=self.name)

    def __eq__(self, other: Any) -> 'Series':
        return Series([x == other for x in self._data], name=self.name)

    def mean(self) -> float:
        vals = [x for x in self._data if isinstance(x, (int, float))]
        return sum(vals) / len(vals) if vals else 0.0

    def sum(self) -> float:
        vals = [x for x in self._data if isinstance(x, (int, float))]
        return sum(vals)

    def to_list(self) -> List[Any]:
        return self._data


class DataFrame:
    """A standard pandas-like DataFrame polyfill."""
    def __init__(self, data: Union[List[Dict[str, Any]], List[List[Any]], Dict[str, List[Any]]] = None, columns: List[str] = None):
        if data is None:
            self._rows = []
            self.columns = columns or []
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                # List of dictionaries
                self.columns = columns or list(data[0].keys())
                self._rows = [[r.get(col) for col in self.columns] for r in data]
            elif data and isinstance(data[0], list):
                # List of lists
                self.columns = columns or [str(i) for i in range(len(data[0]))]
                self._rows = [r.copy() for r in data]
            else:
                self.columns = columns or ["0"]
                self._rows = [[x] for x in data]
        elif isinstance(data, dict):
            # Dictionary of lists
            self.columns = columns or list(data.keys())
            num_rows = max(len(v) for v in data.values()) if data else 0
            self._rows = []
            for i in range(num_rows):
                row = []
                for col in self.columns:
                    val_list = data[col]
                    row.append(val_list[i] if i < len(val_list) else None)
                self._rows.append(row)
        else:
            raise TypeError("Unsupported data format")

    @property
    def shape(self) -> Tuple[int, int]:
        return len(self._rows), len(self.columns)

    @property
    def values(self) -> List[List[Any]]:
        return self._rows

    def head(self, n: int = 5) -> 'DataFrame':
        new_df = DataFrame(columns=self.columns)
        new_df._rows = self._rows[:n]
        return new_df

    def iterrows(self) -> Generator[Tuple[int, Series], None, None]:
        for idx, row in enumerate(self._rows):
            yield idx, Series(row, name=str(idx))

    def to_csv(self, path: str, index: bool = False):
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not index:
                writer.writerow(self.columns)
                writer.writerows(self._rows)
            else:
                writer.writerow(["Index"] + self.columns)
                for idx, row in enumerate(self._rows):
                    writer.writerow([idx] + row)

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            # Extract column
            col_idx = self.columns.index(item)
            return Series([row[col_idx] for row in self._rows], name=item)
        elif isinstance(item, list):
            # Column slice
            new_df = DataFrame(columns=item)
            col_indices = [self.columns.index(c) for c in item]
            new_df._rows = [[row[idx] for idx in col_indices] for row in self._rows]
            return new_df
        elif isinstance(item, Series):
            # Row mask filter
            new_df = DataFrame(columns=self.columns)
            new_df._rows = [row for idx, row in enumerate(self._rows) if item._data[idx]]
            return new_df
        else:
            raise TypeError("Invalid indexing type")

    def __len__(self) -> int:
        return len(self._rows)

    def __str__(self) -> str:
        col_header = "  ".join(self.columns)
        rows_str = "\n".join("  ".join(str(val) for val in row) for row in self._rows[:10])
        suffix = f"\n... ({len(self._rows) - 10} more rows)" if len(self._rows) > 10 else ""
        return f"{col_header}\n{rows_str}{suffix}"

    def __repr__(self) -> str:
        return self.__str__()


def read_csv(filepath_or_buffer: Any, **kwargs) -> DataFrame:
    """Reads a CSV file into a DataFrame polyfill."""
    rows = []
    columns = []
    
    if isinstance(filepath_or_buffer, str):
        with open(filepath_or_buffer, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                columns = next(reader)
            except StopIteration:
                return DataFrame()
            for row in reader:
                rows.append(row)
    else:
        # Buffer-like
        reader = csv.reader(filepath_or_buffer)
        try:
            columns = next(reader)
        except StopIteration:
            return DataFrame()
        for row in reader:
            rows.append(row)

    # Convert numeric types
    for r_idx in range(len(rows)):
        for c_idx in range(len(rows[r_idx])):
            val = rows[r_idx][c_idx]
            try:
                if '.' in val:
                    rows[r_idx][c_idx] = float(val)
                else:
                    rows[r_idx][c_idx] = int(val)
            except ValueError:
                pass

    df = DataFrame(columns=columns)
    df._rows = rows
    return df
