"""Conservative cleaning and type detection for tabular CSV data.

The service deliberately does not apply domain assumptions.  It only removes
structural noise (empty rows/columns and exact duplicates), trims text, and
normalizes values when the whole column supports an unambiguous conversion.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from numbers import Real
from typing import Any

import pandas as pd


_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
)
_CURRENCY_PREFIX = re.compile(r"^(?:r\$|\$)\s*", re.IGNORECASE)
_INTEGER = re.compile(r"^[+-]?\d+$")
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class CleaningReport:
    """Report for one DataFrame, using the API naming convention when serialized."""

    original_rows: int
    final_rows: int
    empty_rows_removed: int
    duplicates_removed: int
    removed_columns: list[str]
    null_values: dict[str, int]
    detected_types: dict[str, str]
    inconsistent_columns: dict[str, list[str]]
    trimmed_text_values: int = 0
    converted_numeric_columns: list[str] | None = None
    normalized_date_columns: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly report for callers outside the service."""

        return {
            "originalRows": self.original_rows,
            "finalRows": self.final_rows,
            "emptyRowsRemoved": self.empty_rows_removed,
            "duplicatesRemoved": self.duplicates_removed,
            "removedColumns": self.removed_columns,
            "nullValues": self.null_values,
            "detectedTypes": self.detected_types,
            "inconsistentColumns": self.inconsistent_columns,
            "trimmedTextValues": self.trimmed_text_values,
            "convertedNumericColumns": self.converted_numeric_columns or [],
            "normalizedDateColumns": self.normalized_date_columns or [],
        }


@dataclass(frozen=True)
class CleaningResult:
    dataframe: pd.DataFrame
    report: CleaningReport


def normalize_column_name(value: Any, position: int) -> str:
    """Normalize only whitespace and provide a name for a blank header.

    Case, accents and punctuation are intentionally preserved.  This avoids
    silently changing a column's meaning or making existing queries harder to
    recognize.
    """

    if value is None or _is_missing(value):
        text = ""
    else:
        text = str(value)
    text = " ".join(text.strip().split())
    return text or f"coluna_{position + 1}"


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
        return bool(result) if not hasattr(result, "__len__") else False
    except (TypeError, ValueError):
        return False


def _normalize_text(value: Any) -> tuple[Any, bool]:
    if _is_missing(value):
        return None, False
    if not isinstance(value, str):
        return value, False
    stripped = value.strip()
    if not stripped:
        return None, stripped != value
    return stripped, stripped != value


def _parse_number(value: Any) -> int | float | None:
    """Parse only unambiguous decimal representations.

    A value such as ``1,234`` is intentionally rejected because it can mean
    either 1.234 or 1234 depending on the locale.  Explicit thousands groups
    (``1.234,56`` or ``1,234.56``) are accepted.
    """

    if isinstance(value, bool) or _is_missing(value):
        return None
    if isinstance(value, Real):
        number = float(value)
        return None if not math.isfinite(number) else number

    text = str(value).strip().replace("\u00a0", " ")
    text = _CURRENCY_PREFIX.sub("", text).replace(" ", "")
    if not text:
        return None

    sign = ""
    if text[0] in "+-":
        sign, text = text[0], text[1:]
    if not text:
        return None

    decimal_separator: str | None = None
    if "," in text and "." in text:
        decimal_separator = "," if text.rfind(",") > text.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        integer_part, fraction = text.rsplit(decimal_separator, 1)
        groups = integer_part.split(thousands_separator)
        if not fraction.isdigit() or not groups[0].isdigit():
            return None
        if any(not group.isdigit() or len(group) != 3 for group in groups[1:]):
            return None
        if len(groups[0]) > 3:
            integer_part = "".join(groups)
        elif len(groups) == 1:
            return None
        else:
            integer_part = "".join(groups)
        normalized = f"{sign}{integer_part}.{fraction}"
    elif "," in text or "." in text:
        separator = "," if "," in text else "."
        if text.count(separator) > 1:
            groups = text.split(separator)
            if not groups[0].isdigit() or any(
                len(group) != 3 or not group.isdigit() for group in groups[1:]
            ):
                return None
            normalized = sign + "".join(groups)
        else:
            integer_part, fraction = text.split(separator)
            if not integer_part.isdigit() or not fraction.isdigit():
                return None
            # A single three-digit separator is locale-ambiguous.
            if len(fraction) == 3:
                return None
            normalized = f"{sign}{integer_part}.{fraction}"
            decimal_separator = separator
    else:
        if not _INTEGER.fullmatch(text):
            return None
        normalized = sign + text

    unsigned_integer = normalized.lstrip("+-").split(".", 1)[0]
    if len(unsigned_integer) > 1 and unsigned_integer.startswith("0"):
        # Preserve likely identifiers such as 000123 rather than turning them
        # into the number 123.
        return None

    try:
        if decimal_separator is None and "." not in normalized:
            return int(normalized)
        number = float(normalized)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _parse_date(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if _is_missing(value):
        return None

    text = str(value).strip()
    if not text:
        return None
    if _DATE_PREFIX.match(text):
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return None


def _format_date(value: datetime, original: Any) -> str:
    text = str(original).strip()
    if "T" in text or " " in text:
        return value.isoformat()
    return value.date().isoformat()


def _classify(value: Any) -> str:
    if _is_missing(value):
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, Real) and not isinstance(value, bool):
        return "number"
    if _parse_date(value) is not None:
        return "date"
    if _parse_number(value) is not None:
        return "number"
    return "string"


class DataCleaningService:
    """Clean one tabular DataFrame without applying domain assumptions."""

    def clean(self, dataframe: pd.DataFrame) -> CleaningResult:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe deve ser uma instância de pandas.DataFrame")

        frame = dataframe.copy(deep=True)
        original_rows = len(frame)
        trimmed_text_values = 0

        normalized_names: list[str] = []
        used_names: set[str] = set()
        for position, original_name in enumerate(frame.columns):
            base_name = normalize_column_name(original_name, position)
            name = base_name
            suffix = 2
            while name in used_names:
                name = f"{base_name}_{suffix}"
                suffix += 1
            used_names.add(name)
            normalized_names.append(name)
        frame.columns = normalized_names

        for column in frame.columns:
            normalized_values: list[Any] = []
            for value in frame[column].tolist():
                normalized_value, was_trimmed = _normalize_text(value)
                trimmed_text_values += int(was_trimmed)
                normalized_values.append(normalized_value)
            frame[column] = pd.Series(normalized_values, index=frame.index, dtype="object")

        frame = frame.dropna(axis=0, how="all")
        empty_rows_removed = original_rows - len(frame)

        removed_columns = [column for column in frame.columns if frame[column].isna().all()]
        if removed_columns:
            frame = frame.drop(columns=removed_columns)

        rows_before_duplicates = len(frame)
        if not frame.empty:
            frame = frame.drop_duplicates(keep="first").reset_index(drop=True)
        duplicates_removed = rows_before_duplicates - len(frame)

        detected_types: dict[str, str] = {}
        inconsistent_columns: dict[str, list[str]] = {}
        converted_numeric_columns: list[str] = []
        normalized_date_columns: list[str] = []

        for column in frame.columns:
            values = [value for value in frame[column].tolist() if not _is_missing(value)]
            observed = sorted({_classify(value) for value in values})
            if not observed:
                detected_types[column] = "unknown"
                continue
            if len(observed) > 1:
                inconsistent_columns[column] = observed
                detected_types[column] = "mixed"
                continue

            detected_type = observed[0]
            detected_types[column] = detected_type
            if detected_type == "number":
                parsed_values = [_parse_number(value) for value in frame[column].tolist()]
                if all(
                    _is_missing(value) or parsed is not None
                    for value, parsed in zip(frame[column], parsed_values)
                ):
                    frame[column] = pd.Series(parsed_values, index=frame.index, dtype="object")
                    converted_numeric_columns.append(column)
            elif detected_type == "date":
                parsed_values = [_parse_date(value) for value in frame[column].tolist()]
                if all(
                    _is_missing(value) or parsed is not None
                    for value, parsed in zip(frame[column], parsed_values)
                ):
                    frame[column] = pd.Series(
                        [
                            None if parsed is None else _format_date(parsed, original)
                            for original, parsed in zip(frame[column], parsed_values)
                        ],
                        index=frame.index,
                        dtype="object",
                    )
                    normalized_date_columns.append(column)

        null_values = {
            column: int(frame[column].isna().sum())
            for column in frame.columns
        }
        report = CleaningReport(
            original_rows=original_rows,
            final_rows=len(frame),
            empty_rows_removed=empty_rows_removed,
            duplicates_removed=duplicates_removed,
            removed_columns=removed_columns,
            null_values=null_values,
            detected_types=detected_types,
            inconsistent_columns=inconsistent_columns,
            trimmed_text_values=trimmed_text_values,
            converted_numeric_columns=converted_numeric_columns,
            normalized_date_columns=normalized_date_columns,
        )
        return CleaningResult(dataframe=frame, report=report)
