"""Ingestão do ZIP e armazenamento em memória dos datasets da sessão.

Porta para Python as regras que já existiam no front-end (mantidas como
fonte de verdade) em:
  - frontend/src/services/ingestion/readZipDataset.ts
  - frontend/src/services/ingestion/parseCsv.ts
  - frontend/src/services/ingestion/inferColumns.ts
  - frontend/src/services/ingestion/decodeText.ts
  - frontend/src/services/ingestion/dataDictionary.ts
  - frontend/src/services/datasetStore.ts

O ZIP é lido inteiramente em memória (nunca é extraído para disco), o que
evita zip-slip/path traversal por construção: não existe caminho de
escrita a partir do nome de um arquivo do pacote.
"""

from __future__ import annotations

import csv
import io
import json
import random
import re
import time
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, BinaryIO

import pandas as pd

from schemas.models import (
    ChatMessage,
    CleaningReport,
    Dataset,
    DatasetColumn,
    DatasetColumnType,
    DatasetTable,
)
from services.data_cleaning_service import (
    DataCleaningService,
    _format_date as format_cleaning_date,
    _parse_date as parse_cleaning_date,
    _parse_number as parse_cleaning_number,
    normalize_column_name,
)

# --- limites de segurança / negócio (espelham o front-end + hardening) ----

MAX_CSV_FILES = 40
PREVIEW_ROWS = 5
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_ENTRY_UNCOMPRESSED_BYTES = 384 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
# A partir deste tamanho, o CSV e lido diretamente do ZIP. Isso evita manter,
# ao mesmo tempo, bytes descompactados, texto, DataFrame e linhas convertidas.
STREAMING_ENTRY_BYTES = 32 * 1024 * 1024
STREAMING_TOTAL_BYTES = 64 * 1024 * 1024

CellValue = str | int | float | bool | None
DataRow = dict[str, CellValue]

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?")
BR_DATE = re.compile(r"^\d{2}/\d{2}/\d{4}")
BOOLEAN_VALUE = re.compile(r"^(true|false|sim|não|nao|0|1)$", re.IGNORECASE)
BOOLEAN_EXPLICIT = re.compile(r"^(true|false|sim|não|nao)$", re.IGNORECASE)
IDENTIFIER_LIKE = re.compile(r"^\d{16,}$")
CURRENCY_HINT = re.compile(r"(valor|preco|preço|total|tributo|custo|montante|desconto)", re.IGNORECASE)
NUMBER_CLEAN = re.compile(r"[R$\s ]", re.IGNORECASE)
NUMBER_SHAPE = re.compile(r"^-?\d*\.?\d+$")


class DatasetIngestionError(Exception):
    """Erro de ingestão com mensagem pronta para exibição ao usuário."""


class DatasetToolError(Exception):
    """Erro de execução de uma tool do agente, com mensagem pronta para ser
    devolvida ao modelo (e, em último caso, ao usuário)."""


# --- ids -----------------------------------------------------------------

_id_counter = 0


def generate_id(prefix: str = "id") -> str:
    global _id_counter
    _id_counter += 1
    timestamp = format(int(time.time() * 1000), "x")
    random_part = format(random.getrandbits(32), "x")[:6]
    return f"{prefix}-{timestamp}-{_id_counter}-{random_part}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# --- decodeText.ts ---------------------------------------------------------


def decode_csv_bytes(data: bytes) -> str:
    """UTF-8 primeiro; se sobrar caractere de substituição, tenta
    Windows-1252 (comum em exportações de sistemas públicos brasileiros)."""
    text = data.decode("utf-8", errors="replace")
    if "�" not in text:
        return text
    return data.decode("windows-1252", errors="replace")


def _strip_bom(text: str) -> str:
    return text[1:] if text.startswith("﻿") else text


# --- parseCsv.ts ------------------------------------------------------------


@dataclass
class ParsedCsv:
    headers: list[str]
    rows: list[dict[str, str]]


def _sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample[:8192], delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        header_line = sample.splitlines()[0] if sample.splitlines() else ""
        comma_count = header_line.count(",")
        semicolon_count = header_line.count(";")
        return ";" if semicolon_count > comma_count else ","


def parse_csv(content: str) -> ParsedCsv:
    stripped = _strip_bom(content)
    if not stripped.strip():
        return ParsedCsv(headers=[], rows=[])

    delimiter = _sniff_delimiter(stripped)
    reader = csv.DictReader(io.StringIO(stripped), delimiter=delimiter)
    raw_headers = reader.fieldnames or []
    header_pairs = [
        (header, header.strip())
        for header in raw_headers
        if header and header.strip()
    ]
    headers = [header for _, header in header_pairs]

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized: dict[str, str] = {}
        for raw_header, header in header_pairs:
            value = raw_row.get(raw_header)
            normalized[header] = value.strip() if isinstance(value, str) else ""
        rows.append(normalized)

    return ParsedCsv(headers=headers, rows=rows)


# --- dataDictionary.ts -------------------------------------------------------


@dataclass
class DictionaryEntry:
    file: str
    column: str
    type: str
    description: str
    key: str
    reference: str
    format: str


@dataclass
class DataDictionary:
    entries: dict[str, dict[str, DictionaryEntry]] = field(default_factory=dict)
    row_count: int = 0


def is_dictionary_file(file_name: str) -> bool:
    base = file_name.lower()
    return "dicionario" in base or "dictionary" in base


def normalize_file_name(value: str) -> str:
    without_path = value.strip().replace("\\", "/").split("/")[-1]
    return without_path.lower()


def _deburr(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.strip().lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _header_picker(headers: list[str]):
    normalized = {_deburr(header): header for header in headers}

    def pick(candidates: list[str]) -> str | None:
        for candidate in candidates:
            match = normalized.get(_deburr(candidate))
            if match:
                return match
        return None

    return pick


def build_data_dictionary(csv_data: ParsedCsv) -> DataDictionary:
    pick = _header_picker(csv_data.headers)

    file_key = pick(["arquivo", "tabela", "file", "table"])
    column_key = pick(["coluna", "campo", "column", "field"])
    type_key = pick(["tipo", "type"])
    description_key = pick(["descricao", "descrição", "description"])
    key_key = pick(["chave", "key"])
    reference_key = pick(["referencia", "referência", "reference"])
    format_key = pick(["formato", "format"])

    dictionary = DataDictionary()
    if not file_key or not column_key:
        return dictionary

    for row in csv_data.rows:
        file_name = normalize_file_name(row.get(file_key, ""))
        column = row.get(column_key, "").strip()
        if not file_name or not column:
            continue

        entry = DictionaryEntry(
            file=file_name,
            column=column,
            type=row.get(type_key, "") if type_key else "",
            description=row.get(description_key, "") if description_key else "",
            key=row.get(key_key, "") if key_key else "",
            reference=row.get(reference_key, "") if reference_key else "",
            format=row.get(format_key, "") if format_key else "",
        )

        dictionary.entries.setdefault(file_name, {})[column] = entry
        dictionary.row_count += 1

    return dictionary


def map_dictionary_type(entry: DictionaryEntry | None) -> DatasetColumnType | None:
    if entry is None:
        return None

    entry_type = entry.type.strip().lower()
    entry_format = entry.format.strip().lower()

    if entry_format in ("brl", "currency") or entry_type in ("currency", "money"):
        return "currency"
    if entry_type in ("datetime", "date", "timestamp", "data"):
        return "date"
    if entry_type in ("integer", "int", "inteiro", "long"):
        return "number"
    if entry_type in ("decimal", "float", "double", "number", "numeric"):
        return "number"
    if entry_type in ("boolean", "bool", "booleano"):
        return "boolean"
    if entry_type in ("string", "text", "texto", "varchar"):
        return "string"
    return None


# --- inferColumns.ts ---------------------------------------------------------


def parse_number(value: str) -> float | None:
    cleaned = NUMBER_CLEAN.sub("", value)
    if cleaned == "" or not any(ch.isdigit() for ch in cleaned):
        return None

    has_comma = "," in cleaned
    has_dot = "." in cleaned
    normalized = cleaned

    if has_comma and has_dot:
        if cleaned.rfind(",") > cleaned.rfind("."):
            normalized = cleaned.replace(".", "").replace(",", ".")
        else:
            normalized = cleaned.replace(",", "")
    elif has_comma:
        normalized = cleaned.replace(",", ".")

    if not NUMBER_SHAPE.match(normalized):
        return None

    try:
        parsed = float(normalized)
    except ValueError:
        return None
    return parsed if parsed == parsed and abs(parsed) != float("inf") else None


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _infer_type(header: str, values: list[Any]) -> DatasetColumnType:
    samples = [str(value) for value in values if not _is_blank(value)][:200]
    if not samples:
        return "unknown"

    if all(ISO_DATE.match(value) or BR_DATE.match(value) for value in samples):
        return "date"

    if all(BOOLEAN_VALUE.match(value) for value in samples) and any(
        BOOLEAN_EXPLICIT.match(value) for value in samples
    ):
        return "boolean"

    looks_like_identifier = any(IDENTIFIER_LIKE.match(value.strip()) for value in samples)

    if not looks_like_identifier and all(parse_number(value) is not None for value in samples):
        return "currency" if CURRENCY_HINT.search(header) else "number"

    return "string"


def build_columns(
    headers: list[str],
    rows: list[dict[str, Any]],
    dictionary: dict[str, DictionaryEntry] | None,
) -> list[DatasetColumn]:
    columns: list[DatasetColumn] = []

    for header in headers:
        entry = dictionary.get(header) if dictionary else None
        declared = map_dictionary_type(entry)
        data_type = declared or _infer_type(header, [row.get(header, "") for row in rows])

        null_count = sum(1 for row in rows if _is_blank(row.get(header)))

        columns.append(
            DatasetColumn(
                name=header,
                dataType=data_type,
                description=(entry.description.strip() if entry and entry.description.strip() else None),
                nullable=null_count > 0,
                nullCount=null_count,
            )
        )

    return columns


def coerce_value(raw: Any, data_type: DatasetColumnType) -> CellValue:
    if raw is None:
        return None
    if isinstance(raw, float) and raw != raw:
        return None
    if isinstance(raw, (int, float, bool)) and data_type in ("number", "currency"):
        return raw

    value = str(raw).strip()
    if value == "":
        return None

    if data_type in ("number", "currency"):
        parsed = parse_number(value)
        return value if parsed is None else parsed

    return value


def coerce_rows(rows: list[dict[str, Any]], columns: list[DatasetColumn]) -> list[DataRow]:
    coerced: list[DataRow] = []
    for row in rows:
        out: DataRow = {}
        for column in columns:
            out[column.name] = coerce_value(row.get(column.name, ""), column.dataType)
        coerced.append(out)
    return coerced


# --- readZipDataset.ts -------------------------------------------------------


def _base_name(path: str) -> str:
    return path.replace("\\", "/").split("/")[-1] or path


def _is_usable_csv(path: str) -> bool:
    if path.endswith("/"):
        return False
    name = _base_name(path)
    if name.startswith(".") or path.startswith("__MACOSX/"):
        return False
    return name.lower().endswith(".csv")


def _to_table_id(file_name: str) -> str:
    return re.sub(r"\.csv$", "", file_name, flags=re.IGNORECASE).strip() or "tabela"


def _dataset_name_from_file(file_name: str) -> str:
    base = re.sub(r"\.(?:zip|csv)$", "", file_name, flags=re.IGNORECASE)
    base = re.sub(r"[_-]+", " ", base).strip()
    if not base:
        return "Conjunto de dados"
    return base[0].upper() + base[1:]


def _describe_table(column_names: list[str]) -> str:
    preview = ", ".join(column_names[:4])
    rest = len(column_names) - 4
    return f"{preview} e mais {rest} colunas." if rest > 0 else f"{preview}."


def _build_summary(tables: list[DatasetTable], dictionary: DataDictionary) -> str:
    table_list = ", ".join(table.name for table in tables)
    total_columns = sum(table.columnCount for table in tables)
    if dictionary.row_count:
        dictionary_note = f" O dicionário de dados descreve {dictionary.row_count} colunas."
    else:
        dictionary_note = " Nenhum dicionário de dados foi encontrado: os tipos foram inferidos a partir dos valores."
    return (
        f"Foram lidas {len(tables)} tabelas ({table_list}), somando {total_columns} colunas."
        f"{dictionary_note}"
    )


def _read_zip_entries(stream: BinaryIO) -> dict[str, bytes]:
    """Lê o ZIP inteiramente em memória, com defesas contra zip bomb e
    contra qualquer tentativa de path traversal (nunca gravamos em disco;
    nomes suspeitos, mesmo assim, são descartados antes de ler os bytes)."""
    try:
        archive = zipfile.ZipFile(stream)
        bad_entry = archive.testzip()
        if bad_entry is not None:
            raise DatasetIngestionError(
                "Não foi possível abrir o arquivo. Confirme que ele é um .zip válido e não está protegido por senha."
            )
    except zipfile.BadZipFile as exc:
        raise DatasetIngestionError(
            "Não foi possível abrir o arquivo. Confirme que ele é um .zip válido e não está protegido por senha."
        ) from exc

    total_uncompressed = 0
    files: dict[str, bytes] = {}

    for info in archive.infolist():
        name = info.filename
        if info.is_dir():
            continue
        # Guarda contra path traversal mesmo sem nunca extrair para disco.
        if name.startswith("/") or ".." in name.replace("\\", "/").split("/"):
            continue
        if info.file_size > MAX_ENTRY_UNCOMPRESSED_BYTES:
            raise DatasetIngestionError(
                "Um dos arquivos dentro do ZIP excede o tamanho máximo permitido."
            )
        if info.file_size and info.file_size / max(info.compress_size, 1) > MAX_COMPRESSION_RATIO:
            raise DatasetIngestionError(
                "O ZIP possui uma taxa de compactação fora do limite de segurança."
            )
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise DatasetIngestionError(
                "O conteúdo descompactado do ZIP excede o limite de 512 MB."
            )
        files[name] = archive.read(info)

    return files


def _validated_csv_infos(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """Valida metadados do ZIP sem descompactar entradas grandes em memória."""

    csv_infos: list[zipfile.ZipInfo] = []
    total_uncompressed = 0

    for info in archive.infolist():
        name = info.filename
        if info.is_dir():
            continue
        if name.startswith("/") or ".." in name.replace("\\", "/").split("/"):
            continue
        if info.flag_bits & 0x1:
            raise DatasetIngestionError(
                "Não foi possível abrir o arquivo. Confirme que ele não está protegido por senha."
            )
        if info.file_size > MAX_ENTRY_UNCOMPRESSED_BYTES:
            raise DatasetIngestionError(
                "Um dos arquivos dentro do ZIP excede o limite descompactado de 384 MB."
            )
        if info.file_size and info.file_size / max(info.compress_size, 1) > MAX_COMPRESSION_RATIO:
            raise DatasetIngestionError(
                "O ZIP possui uma taxa de compactação fora do limite de segurança."
            )
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise DatasetIngestionError(
                "O conteúdo descompactado do ZIP excede o limite de 512 MB."
            )
        if _is_usable_csv(name):
            csv_infos.append(info)

    if not csv_infos:
        raise DatasetIngestionError(
            "Nenhum arquivo .csv foi encontrado dentro do ZIP. Verifique o conteúdo do pacote e envie novamente."
        )
    if len(csv_infos) > MAX_CSV_FILES:
        raise DatasetIngestionError(
            f"O ZIP contém {len(csv_infos)} arquivos CSV. O limite por conjunto de dados é de {MAX_CSV_FILES}."
        )
    return csv_infos


@dataclass
class IngestedDataset:
    dataset: Dataset
    rows: dict[str, list[DataRow]]
    cleaning_reports: dict[str, CleaningReport] = field(default_factory=dict)


@dataclass
class _StreamedTable:
    headers: list[str]
    rows: list[DataRow]
    columns: list[DatasetColumn]
    report: CleaningReport


def _csv_encoding(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    with archive.open(info) as raw:
        sample = raw.read(64 * 1024)
    try:
        sample.decode("utf-8", errors="strict")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "windows-1252"


def _unique_headers(raw_headers: list[str]) -> list[str]:
    headers: list[str] = []
    used: set[str] = set()
    for position, raw_header in enumerate(raw_headers):
        base = normalize_column_name(raw_header, position)
        header = base
        suffix = 2
        while header in used:
            header = f"{base}_{suffix}"
            suffix += 1
        used.add(header)
        headers.append(header)
    return headers


def _read_streamed_table(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    table_dictionary: dict[str, DictionaryEntry] | None,
) -> _StreamedTable | None:
    """Lê uma entrada grande linha a linha e mantém apenas a representação final."""

    encoding = _csv_encoding(archive, info)
    with archive.open(info) as sample_raw:
        sample = sample_raw.read(64 * 1024).decode(encoding, errors="replace")
    delimiter = _sniff_delimiter(sample)

    original_rows = 0
    empty_rows_removed = 0
    duplicates_removed = 0
    trimmed_text_values = 0
    raw_rows: list[tuple[str | None, ...] | DataRow] = []
    seen_rows: set[tuple[str | None, ...]] = set()

    with archive.open(info) as raw:
        text_stream = io.TextIOWrapper(raw, encoding=encoding, errors="replace", newline="")
        reader = csv.reader(text_stream, delimiter=delimiter)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return None

        headers = _unique_headers(raw_headers)
        if not headers:
            return None
        non_empty_columns = [False] * len(headers)
        null_counts = [0] * len(headers)
        samples: list[list[str]] = [[] for _ in headers]

        for raw_values in reader:
            original_rows += 1
            values: list[str | None] = []
            for position in range(len(headers)):
                raw_value = raw_values[position] if position < len(raw_values) else ""
                value = raw_value.strip()
                trimmed_text_values += int(value != raw_value)
                values.append(value or None)

            if not any(value is not None for value in values):
                empty_rows_removed += 1
                continue

            row_key = tuple(values)
            if row_key in seen_rows:
                duplicates_removed += 1
                continue
            seen_rows.add(row_key)
            raw_rows.append(row_key)

            for position, value in enumerate(values):
                if value is None:
                    null_counts[position] += 1
                    continue
                non_empty_columns[position] = True
                if len(samples[position]) < 200:
                    samples[position].append(value)

    # As tuplas usadas para deduplicação apontam para os mesmos textos das
    # linhas; liberá-las antes da conversão evita um pico grande de memória.
    seen_rows.clear()

    active_positions = [index for index, present in enumerate(non_empty_columns) if present]
    active_headers = [headers[index] for index in active_positions]
    if not active_headers:
        return None

    aligned_dictionary = _align_dictionary(table_dictionary, active_headers)
    columns: list[DatasetColumn] = []
    detected_types: dict[str, str] = {}
    converted_numeric: list[str] = []
    normalized_dates: list[str] = []

    for position in active_positions:
        header = headers[position]
        entry = aligned_dictionary.get(header) if aligned_dictionary else None
        declared = map_dictionary_type(entry)
        data_type = declared or _infer_type(header, samples[position])
        detected = _infer_type(header, samples[position])
        detected_types[header] = detected
        if detected in ("number", "currency"):
            converted_numeric.append(header)
        elif detected == "date":
            normalized_dates.append(header)
        columns.append(
            DatasetColumn(
                name=header,
                dataType=data_type,
                description=(entry.description.strip() if entry and entry.description.strip() else None),
                nullable=null_counts[position] > 0,
                nullCount=null_counts[position],
            )
        )

    column_by_header = {column.name: column for column in columns}
    for row_index, raw_row in enumerate(raw_rows):
        assert isinstance(raw_row, tuple)
        converted: DataRow = {}
        for position in active_positions:
            header = headers[position]
            value: Any = raw_row[position]
            if value is not None and detected_types[header] in ("number", "currency"):
                parsed_number = parse_cleaning_number(value)
                if parsed_number is not None:
                    value = parsed_number
            elif value is not None and detected_types[header] == "date":
                parsed_date = parse_cleaning_date(value)
                if parsed_date is not None:
                    value = format_cleaning_date(parsed_date, value)
            converted[header] = coerce_value(value, column_by_header[header].dataType)
        raw_rows[row_index] = converted

    final_rows = [row for row in raw_rows if isinstance(row, dict)]
    removed_columns = [header for index, header in enumerate(headers) if not non_empty_columns[index]]
    report = CleaningReport(
        originalRows=original_rows,
        finalRows=len(final_rows),
        emptyRowsRemoved=empty_rows_removed,
        duplicatesRemoved=duplicates_removed,
        removedColumns=removed_columns,
        nullValues={headers[index]: null_counts[index] for index in active_positions},
        detectedTypes=detected_types,
        inconsistentColumns={},
        trimmedTextValues=trimmed_text_values,
        convertedNumericColumns=converted_numeric,
        normalizedDateColumns=normalized_dates,
    )
    return _StreamedTable(
        headers=active_headers,
        rows=final_rows,
        columns=columns,
        report=report,
    )


def _rows_from_dataframe(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert cleaned pandas values to the JSON-like rows used by the store."""

    rows: list[dict[str, Any]] = []
    for raw_row in dataframe.to_dict(orient="records"):
        row: dict[str, Any] = {}
        for column, value in raw_row.items():
            if value is None:
                row[column] = None
                continue
            try:
                missing = pd.isna(value)
                if not hasattr(missing, "__len__") and bool(missing):
                    row[column] = None
                    continue
            except (TypeError, ValueError):
                pass
            row[column] = value
        rows.append(row)
    return rows


def _align_dictionary(
    table_dictionary: dict[str, DictionaryEntry] | None, headers: list[str]
) -> dict[str, DictionaryEntry] | None:
    """Match dictionary columns after the cleaner's conservative normalization."""

    if not table_dictionary:
        return None

    normalized_entries = {
        normalize_column_name(name, position): entry
        for position, (name, entry) in enumerate(table_dictionary.items())
    }
    aligned: dict[str, DictionaryEntry] = {}
    for position, header in enumerate(headers):
        entry = normalized_entries.get(normalize_column_name(header, position))
        if entry is not None:
            aligned[header] = entry
    return aligned or None


def _build_ingested_dataset(
    file_name: str,
    file_size: int,
    csv_entries: list[tuple[str, bytes]],
    *,
    allow_dictionary: bool,
) -> IngestedDataset:
    """Build a dataset from one or more already decoded CSV entries."""

    dictionary_entry = (
        next(
            (entry for entry in csv_entries if is_dictionary_file(_base_name(entry[0]))),
            None,
        )
        if allow_dictionary
        else None
    )
    if dictionary_entry:
        dictionary = build_data_dictionary(parse_csv(decode_csv_bytes(dictionary_entry[1])))
    else:
        dictionary = DataDictionary()

    table_entries = (
        [entry for entry in csv_entries if not is_dictionary_file(_base_name(entry[0]))]
        if allow_dictionary
        else csv_entries
    )

    if not table_entries:
        raise DatasetIngestionError(
            "O ZIP contém apenas o dicionário de dados. Inclua ao menos um arquivo CSV com registros."
        )

    tables: list[DatasetTable] = []
    rows_by_table: dict[str, list[DataRow]] = {}
    cleaning_reports: dict[str, CleaningReport] = {}
    cleaning_service = DataCleaningService()
    used_table_ids: set[str] = set()

    for name, data in table_entries:
        file_name_only = _base_name(name)
        csv_data = parse_csv(decode_csv_bytes(data))

        if not csv_data.headers:
            continue

        raw_dataframe = pd.DataFrame(csv_data.rows, columns=csv_data.headers)
        cleaned = cleaning_service.clean(raw_dataframe)
        cleaned_headers = [str(header) for header in cleaned.dataframe.columns]
        if not cleaned_headers:
            continue

        cleaned_rows = _rows_from_dataframe(cleaned.dataframe)
        table_dictionary = _align_dictionary(
            dictionary.entries.get(normalize_file_name(file_name_only)), cleaned_headers
        )
        columns = build_columns(cleaned_headers, cleaned_rows, table_dictionary)
        coerced = coerce_rows(cleaned_rows, columns)
        base_table_id = _to_table_id(file_name_only)
        table_id = base_table_id
        suffix = 2
        while table_id in used_table_ids:
            table_id = f"{base_table_id}_{suffix}"
            suffix += 1
        used_table_ids.add(table_id)
        cleaning_report = CleaningReport(**cleaned.report.as_dict())

        tables.append(
            DatasetTable(
                id=table_id,
                name=table_id,
                fileName=file_name_only,
                description=_describe_table([column.name for column in columns]),
                rowCount=len(coerced),
                columnCount=len(columns),
                columns=columns,
                preview=coerced[:PREVIEW_ROWS],
            )
        )
        rows_by_table[table_id] = coerced
        cleaning_reports[table_id] = cleaning_report

    if not tables:
        raise DatasetIngestionError(
            "Não foi possível ler nenhuma tabela: os arquivos CSV estão vazios ou sem cabeçalho."
        )

    tables.sort(key=lambda table: table.rowCount, reverse=True)

    dataset = Dataset(
        id=generate_id("ds"),
        name=_dataset_name_from_file(file_name),
        uploadedAt=_now_iso(),
        status="ready",
        totalRows=sum(table.rowCount for table in tables),
        totalColumns=sum(table.columnCount for table in tables),
        tables=tables,
        sourceFileName=file_name,
        sourceFileSize=file_size,
        dictionaryFileName=_base_name(dictionary_entry[0]) if dictionary_entry else None,
        summary=_build_summary(tables, dictionary),
        cleaningReport=cleaning_reports,
    )

    return IngestedDataset(
        dataset=dataset, rows=rows_by_table, cleaning_reports=cleaning_reports
    )


def _build_streamed_zip_dataset(
    file_name: str,
    file_size: int,
    archive: zipfile.ZipFile,
    csv_infos: list[zipfile.ZipInfo],
) -> IngestedDataset:
    """Monta datasets grandes lendo uma entrada do ZIP por vez."""

    dictionary_info = next(
        (info for info in csv_infos if is_dictionary_file(_base_name(info.filename))),
        None,
    )
    if dictionary_info is not None:
        dictionary = build_data_dictionary(
            parse_csv(decode_csv_bytes(archive.read(dictionary_info)))
        )
    else:
        dictionary = DataDictionary()

    table_infos = [
        info
        for info in csv_infos
        if not is_dictionary_file(_base_name(info.filename))
    ]
    if not table_infos:
        raise DatasetIngestionError(
            "O ZIP contém apenas o dicionário de dados. Inclua ao menos um arquivo CSV com registros."
        )

    tables: list[DatasetTable] = []
    rows_by_table: dict[str, list[DataRow]] = {}
    cleaning_reports: dict[str, CleaningReport] = {}
    used_table_ids: set[str] = set()

    for info in table_infos:
        table_file_name = _base_name(info.filename)
        streamed = _read_streamed_table(
            archive,
            info,
            dictionary.entries.get(normalize_file_name(table_file_name)),
        )
        if streamed is None:
            continue

        base_table_id = _to_table_id(table_file_name)
        table_id = base_table_id
        suffix = 2
        while table_id in used_table_ids:
            table_id = f"{base_table_id}_{suffix}"
            suffix += 1
        used_table_ids.add(table_id)

        tables.append(
            DatasetTable(
                id=table_id,
                name=table_id,
                fileName=table_file_name,
                description=_describe_table(streamed.headers),
                rowCount=len(streamed.rows),
                columnCount=len(streamed.columns),
                columns=streamed.columns,
                preview=streamed.rows[:PREVIEW_ROWS],
            )
        )
        rows_by_table[table_id] = streamed.rows
        cleaning_reports[table_id] = streamed.report

    if not tables:
        raise DatasetIngestionError(
            "Não foi possível ler nenhuma tabela: os arquivos CSV estão vazios ou sem cabeçalho."
        )

    tables.sort(key=lambda table: table.rowCount, reverse=True)
    dataset = Dataset(
        id=generate_id("ds"),
        name=_dataset_name_from_file(file_name),
        uploadedAt=_now_iso(),
        status="ready",
        totalRows=sum(table.rowCount for table in tables),
        totalColumns=sum(table.columnCount for table in tables),
        tables=tables,
        sourceFileName=file_name,
        sourceFileSize=file_size,
        dictionaryFileName=(
            _base_name(dictionary_info.filename) if dictionary_info is not None else None
        ),
        summary=_build_summary(tables, dictionary),
        cleaningReport=cleaning_reports,
    )
    return IngestedDataset(
        dataset=dataset,
        rows=rows_by_table,
        cleaning_reports=cleaning_reports,
    )


def ingest_file(file_name: str, file_size: int, content: bytes) -> IngestedDataset:
    """Ingest either one CSV file or a ZIP containing CSV files."""

    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return _build_ingested_dataset(
            file_name,
            file_size,
            [(file_name, content)],
            allow_dictionary=False,
        )
    if lower_name.endswith(".zip"):
        return ingest_zip(file_name, file_size, content)
    raise DatasetIngestionError("Envie um arquivo .csv ou .zip.")


def ingest_zip(file_name: str, file_size: int, content: bytes) -> IngestedDataset:
    """Read a ZIP safely, streaming large CSV entries to control memory use."""

    if not file_name.lower().endswith(".zip"):
        raise DatasetIngestionError("Envie um arquivo .zip.")

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            csv_infos = _validated_csv_infos(archive)
            total_size = sum(info.file_size for info in csv_infos)
            use_streaming = (
                total_size >= STREAMING_TOTAL_BYTES
                or any(info.file_size >= STREAMING_ENTRY_BYTES for info in csv_infos)
            )
            if use_streaming:
                return _build_streamed_zip_dataset(
                    file_name,
                    file_size,
                    archive,
                    csv_infos,
                )

            csv_entries = [(info.filename, archive.read(info)) for info in csv_infos]
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise DatasetIngestionError(
            "Não foi possível abrir o arquivo. Confirme que ele é um .zip válido e não está protegido por senha."
        ) from exc

    return _build_ingested_dataset(file_name, file_size, csv_entries, allow_dictionary=True)


# --- datasetStore.ts (em memória, por processo) -----------------------------


@dataclass
class _StoredDataset:
    dataset: Dataset
    rows: dict[str, list[DataRow]]
    history: list[ChatMessage] = field(default_factory=list)


class _DatasetStore:
    """Store em memória, escopada ao processo do backend. Não há banco de
    dados porque nada aqui precisa sobreviver a um restart: o front-end já
    trata o dataset como pertencente à sessão de upload atual (ver README,
    seção 'Serviço de dados')."""

    def __init__(self) -> None:
        self._data: dict[str, _StoredDataset] = {}

    def save(self, dataset: Dataset, rows: dict[str, list[DataRow]]) -> None:
        self._data[dataset.id] = _StoredDataset(dataset=dataset, rows=rows)

    def get_dataset(self, dataset_id: str) -> Dataset | None:
        stored = self._data.get(dataset_id)
        return stored.dataset if stored else None

    def has(self, dataset_id: str) -> bool:
        return dataset_id in self._data

    def rows_by_table(self, dataset_id: str) -> dict[str, list[DataRow]]:
        stored = self._data.get(dataset_id)
        return stored.rows if stored else {}

    def history(self, dataset_id: str) -> list[ChatMessage]:
        stored = self._data.get(dataset_id)
        if not stored:
            return []
        return sorted(stored.history, key=lambda item: item.createdAt, reverse=True)

    def add_history(self, dataset_id: str, message: ChatMessage) -> None:
        stored = self._data.get(dataset_id)
        if not stored:
            return
        stored.history.insert(0, message)

    def remove_history(self, dataset_id: str, message_id: str) -> None:
        stored = self._data.get(dataset_id)
        if not stored:
            return
        stored.history = [item for item in stored.history if item.id != message_id]


store = _DatasetStore()


# --- tools do agente (consultas sobre um dataset já carregado) -------------

# Respostas de tools são contexto da LLM, não exportações de dados. Manter
# esse limite baixo evita que uma tabela larga estoure o limite de tokens da
# Groq durante a próxima rodada do agente.
MAX_TOOL_ROWS = 10
MAX_TOOL_RESULT_CHARS = 7_000
MAX_TOOL_ROW_CHARS = 1_800
MAX_TOOL_CELL_CHARS = 160
_FILTER_OPERATORS = ("=", "!=", ">", "<", ">=", "<=", "contains")


def _compact_tool_value(value: Any) -> Any:
    """Reduz valores textuais muito longos no payload enviado à LLM."""

    if isinstance(value, str) and len(value) > MAX_TOOL_CELL_CHARS:
        return f"{value[:MAX_TOOL_CELL_CHARS]}…"
    return value


def _compact_tool_row(row: DataRow) -> DataRow:
    """Mantém uma linha completa enquanto ela couber no orçamento seguro."""

    compact_row: DataRow = {}
    for key, value in row.items():
        candidate = {**compact_row, key: _compact_tool_value(value)}
        candidate_size = len(json.dumps(candidate, ensure_ascii=False, default=str))
        if candidate_size > MAX_TOOL_ROW_CHARS:
            compact_row["__omittedColumns"] = len(row) - len(compact_row)
            break
        compact_row[key] = _compact_tool_value(value)
    return compact_row


def _bounded_tool_rows(rows: list[DataRow]) -> tuple[list[DataRow], bool]:
    """Retorna uma amostra pequena e limitada por caracteres.

    O dataset original permanece intacto no store. A limitação vale apenas
    para o contexto da LLM e informa ao agente quando há dados omitidos.
    """

    selected: list[DataRow] = []
    encoded_size = 2

    for row in rows[:MAX_TOOL_ROWS]:
        compact_row = _compact_tool_row(row)
        row_size = len(json.dumps(compact_row, ensure_ascii=False, default=str))
        if selected and encoded_size + row_size + 1 > MAX_TOOL_RESULT_CHARS:
            break
        selected.append(compact_row)
        encoded_size += row_size + 1

    truncated = len(selected) < len(rows)
    return selected, truncated


def _get_dataset_or_raise(dataset_id: str) -> Dataset:
    dataset = store.get_dataset(dataset_id)
    if dataset is None:
        raise DatasetToolError("Dataset não encontrado.")
    return dataset


def _find_table(dataset: Dataset, table_ref: str) -> DatasetTable:
    for table in dataset.tables:
        if table.id == table_ref or table.name == table_ref:
            return table
    available = ", ".join(table.name for table in dataset.tables)
    raise DatasetToolError(
        f"Tabela '{table_ref}' não existe neste dataset. Tabelas disponíveis: {available}."
    )


def _find_column(table: DatasetTable, column_ref: str) -> DatasetColumn:
    for column in table.columns:
        if column.name == column_ref:
            return column
    available = ", ".join(column.name for column in table.columns)
    raise DatasetToolError(
        f"Coluna '{column_ref}' não existe na tabela '{table.name}'. Colunas disponíveis: {available}."
    )


def _column_info(column: DatasetColumn) -> dict[str, Any]:
    return {
        "name": column.name,
        "dataType": column.dataType,
        "description": column.description,
        "nullable": column.nullable,
        "nullCount": column.nullCount,
    }


def listar_colunas(dataset_id: str, table: str | None = None) -> dict[str, Any]:
    """Lista as colunas de uma tabela do dataset, ou de todas as tabelas se
    `table` for None."""
    dataset = _get_dataset_or_raise(dataset_id)

    if table is not None:
        found = _find_table(dataset, table)
        return {"table": found.name, "columns": [_column_info(column) for column in found.columns]}

    return {
        "tables": [
            {"table": t.name, "columns": [_column_info(column) for column in t.columns]}
            for t in dataset.tables
        ]
    }


def obter_resumo(dataset_id: str) -> dict[str, Any]:
    """Resumo do dataset: nome, tabelas, totais de linhas/colunas e descrição
    textual gerada na ingestão."""
    dataset = _get_dataset_or_raise(dataset_id)
    return {
        "datasetName": dataset.name,
        "summary": dataset.summary,
        "totalRows": dataset.totalRows,
        "totalColumns": dataset.totalColumns,
        "tables": [
            {
                "table": t.name,
                "rowCount": t.rowCount,
                "columnCount": t.columnCount,
                "description": t.description,
            }
            for t in dataset.tables
        ],
    }


def buscar_registros(
    dataset_id: str, table: str, limit: int = 10, offset: int = 0
) -> dict[str, Any]:
    """Amostra de linhas de uma tabela (limit entre 1 e 10, offset >= 0)."""
    dataset = _get_dataset_or_raise(dataset_id)
    found = _find_table(dataset, table)

    safe_limit = max(1, min(limit, MAX_TOOL_ROWS))
    safe_offset = max(0, offset)

    rows = store.rows_by_table(dataset_id).get(found.id, [])
    page = rows[safe_offset : safe_offset + safe_limit]
    bounded_rows, truncated = _bounded_tool_rows(page)

    return {
        "table": found.name,
        "totalRows": len(rows),
        "returned": len(bounded_rows),
        "hasMore": truncated or safe_offset + len(page) < len(rows),
        "rows": bounded_rows,
    }


def _normalize_date(value: CellValue) -> CellValue:
    """Normaliza uma data (ISO `yyyy-mm-dd` ou BR `dd/mm/yyyy`, com ou sem
    horário) para a forma `yyyy-mm-dd`, de modo que a comparação
    lexicográfica de strings coincida com a ordem cronológica. Valores que
    não batem com nenhum dos dois formatos (ou não são string) voltam
    inalterados, em vez de lançar uma exceção."""
    if not isinstance(value, str):
        return value
    if BR_DATE.match(value):
        day, month, year = value[:10].split("/")
        return f"{year}-{month}-{day}"
    if ISO_DATE.match(value):
        return value[:10]
    return value


def _coerce_filter_value(raw: str, data_type: DatasetColumnType) -> CellValue:
    if data_type in ("number", "currency"):
        parsed = parse_number(raw)
        return raw if parsed is None else parsed
    if data_type == "date":
        return _normalize_date(raw)
    return raw


def _matches(cell: CellValue, operator: str, target: CellValue) -> bool:
    if operator == "contains":
        return isinstance(cell, str) and isinstance(target, str) and target.lower() in cell.lower()
    if cell is None:
        return False
    try:
        if operator == "=":
            return cell == target
        if operator == "!=":
            return cell != target
        if operator == ">":
            return cell > target
        if operator == "<":
            return cell < target
        if operator == ">=":
            return cell >= target
        if operator == "<=":
            return cell <= target
    except TypeError:
        return False
    return False


def filtrar_dados(
    dataset_id: str, table: str, column: str, operator: str, value: str
) -> dict[str, Any]:
    """Linhas de uma tabela cuja `column` satisfaz `operator` em relação a
    `value`. Devolve no máximo 10 linhas compactadas, mas informa o total de
    acertos."""
    if operator not in _FILTER_OPERATORS:
        raise DatasetToolError(
            f"Operador '{operator}' inválido. Use um de: {', '.join(_FILTER_OPERATORS)}."
        )

    dataset = _get_dataset_or_raise(dataset_id)
    found_table = _find_table(dataset, table)
    found_column = _find_column(found_table, column)

    target = _coerce_filter_value(value, found_column.dataType)
    rows = store.rows_by_table(dataset_id).get(found_table.id, [])
    if found_column.dataType == "date":
        matches = [
            row for row in rows if _matches(_normalize_date(row.get(column)), operator, target)
        ]
    else:
        matches = [row for row in rows if _matches(row.get(column), operator, target)]

    bounded_rows, truncated = _bounded_tool_rows(matches)

    return {
        "table": found_table.name,
        "column": column,
        "operator": operator,
        "value": value,
        "totalMatches": len(matches),
        "returned": len(bounded_rows),
        "hasMore": truncated,
        "rows": bounded_rows,
    }


def calcular_estatisticas(dataset_id: str, table: str, column: str) -> dict[str, Any]:
    """Estatísticas de uma coluna: numérica/moeda devolve
    count/sum/avg/min/max/nullCount; texto devolve distinctCount e os 5
    valores mais frequentes (topValues)."""
    dataset = _get_dataset_or_raise(dataset_id)
    found_table = _find_table(dataset, table)
    found_column = _find_column(found_table, column)

    rows = store.rows_by_table(dataset_id).get(found_table.id, [])
    raw_values = [row.get(column) for row in rows]
    values = [value for value in raw_values if value is not None]
    null_count = len(raw_values) - len(values)

    if found_column.dataType in ("number", "currency"):
        numeric = [value for value in values if isinstance(value, (int, float))]
        total = sum(numeric)
        return {
            "table": found_table.name,
            "column": column,
            "count": len(numeric),
            "nullCount": null_count,
            "nonNumericCount": len(values) - len(numeric),
            "sum": total,
            "avg": total / len(numeric) if numeric else None,
            "min": min(numeric) if numeric else None,
            "max": max(numeric) if numeric else None,
        }

    counts = Counter(str(value) for value in values)
    top_values = [{"value": value, "count": count} for value, count in counts.most_common(5)]
    return {
        "table": found_table.name,
        "column": column,
        "count": len(values),
        "nullCount": null_count,
        "distinctCount": len(counts),
        "topValues": top_values,
    }


class DatasetService:
    """Fachada injetável para as consultas usadas pelo agente.

    As funções de módulo acima continuam sendo a fonte de verdade e são
    preservadas para compatibilidade com os testes e demais consumidores.
    Esta fachada só permite que o agente receba explicitamente o serviço por
    dependência, sem recorrer a estado global dentro das tools.
    """

    def listar_colunas(self, dataset_id: str, table: str | None = None) -> dict[str, Any]:
        return listar_colunas(dataset_id, table)

    def obter_resumo(self, dataset_id: str) -> dict[str, Any]:
        return obter_resumo(dataset_id)

    def buscar_registros(
        self, dataset_id: str, table: str, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        return buscar_registros(dataset_id, table, limit, offset)

    def filtrar_dados(
        self, dataset_id: str, table: str, column: str, operator: str, value: str
    ) -> dict[str, Any]:
        return filtrar_dados(dataset_id, table, column, operator, value)

    def calcular_estatisticas(self, dataset_id: str, table: str, column: str) -> dict[str, Any]:
        return calcular_estatisticas(dataset_id, table, column)
