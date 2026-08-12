"""Ingestão do ZIP e armazenamento em memória dos datasets da sessão.

Porta para Python as regras que já existiam no front-end (mantidas como
fonte de verdade) em:
  - src/services/ingestion/readZipDataset.ts
  - src/services/ingestion/parseCsv.ts
  - src/services/ingestion/inferColumns.ts
  - src/services/ingestion/decodeText.ts
  - src/services/ingestion/dataDictionary.ts
  - src/services/datasetStore.ts

O ZIP é lido inteiramente em memória (nunca é extraído para disco), o que
evita zip-slip/path traversal por construção: não existe caminho de
escrita a partir do nome de um arquivo do pacote.
"""

from __future__ import annotations

import csv
import io
import random
import re
import time
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, BinaryIO

from schemas.models import ChatMessage, Dataset, DatasetColumn, DatasetColumnType, DatasetTable

# --- limites de segurança / negócio (espelham o front-end + hardening) ----

MAX_CSV_FILES = 40
PREVIEW_ROWS = 5
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB, mesmo limite anunciado no upload
MAX_ENTRY_UNCOMPRESSED_BYTES = 100 * 1024 * 1024

CellValue = str | float | None
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
    headers = [header.strip() for header in raw_headers if header and header.strip()]

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized: dict[str, str] = {}
        for header in headers:
            value = raw_row.get(header)
            normalized[header] = value.strip() if isinstance(value, str) else ""
        if any(normalized[header] != "" for header in headers):
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


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _infer_type(header: str, values: list[str]) -> DatasetColumnType:
    samples = [value for value in values if not _is_blank(value)][:200]
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
    rows: list[dict[str, str]],
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


def coerce_value(raw: str, data_type: DatasetColumnType) -> CellValue:
    value = raw.strip()
    if value == "":
        return None

    if data_type in ("number", "currency"):
        parsed = parse_number(value)
        return value if parsed is None else parsed

    return value


def coerce_rows(rows: list[dict[str, str]], columns: list[DatasetColumn]) -> list[DataRow]:
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
    base = re.sub(r"\.zip$", "", file_name, flags=re.IGNORECASE)
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
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise DatasetIngestionError(
                "O conteúdo descompactado do ZIP excede o limite de 200 MB."
            )
        files[name] = archive.read(info)

    return files


@dataclass
class IngestedDataset:
    dataset: Dataset
    rows: dict[str, list[DataRow]]


def ingest_zip(file_name: str, file_size: int, content: bytes) -> IngestedDataset:
    """Equivalente a `readZipDataset.ts`: recebe os bytes do ZIP já lidos em
    memória (o endpoint faz `await file.read()`) e devolve o `Dataset` no
    mesmo formato que o front-end já espera."""
    if not file_name.lower().endswith(".zip"):
        raise DatasetIngestionError("Envie um arquivo .zip.")

    files = _read_zip_entries(io.BytesIO(content))
    csv_entries = [(name, data) for name, data in files.items() if _is_usable_csv(name)]

    if not csv_entries:
        raise DatasetIngestionError(
            "Nenhum arquivo .csv foi encontrado dentro do ZIP. Verifique o conteúdo do pacote e envie novamente."
        )

    if len(csv_entries) > MAX_CSV_FILES:
        raise DatasetIngestionError(
            f"O ZIP contém {len(csv_entries)} arquivos CSV. O limite por conjunto de dados é de {MAX_CSV_FILES}."
        )

    dictionary_entry = next(
        (entry for entry in csv_entries if is_dictionary_file(_base_name(entry[0]))), None
    )
    if dictionary_entry:
        dictionary = build_data_dictionary(parse_csv(decode_csv_bytes(dictionary_entry[1])))
    else:
        dictionary = DataDictionary()

    table_entries = [
        entry for entry in csv_entries if not is_dictionary_file(_base_name(entry[0]))
    ]

    if not table_entries:
        raise DatasetIngestionError(
            "O ZIP contém apenas o dicionário de dados. Inclua ao menos um arquivo CSV com registros."
        )

    tables: list[DatasetTable] = []
    rows_by_table: dict[str, list[DataRow]] = {}

    for name, data in table_entries:
        file_name_only = _base_name(name)
        csv_data = parse_csv(decode_csv_bytes(data))

        if not csv_data.headers:
            continue

        table_dictionary = dictionary.entries.get(normalize_file_name(file_name_only))
        columns = build_columns(csv_data.headers, csv_data.rows, table_dictionary)
        coerced = coerce_rows(csv_data.rows, columns)
        table_id = _to_table_id(file_name_only)

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
    )

    return IngestedDataset(dataset=dataset, rows=rows_by_table)


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

MAX_TOOL_ROWS = 50
_FILTER_OPERATORS = ("=", "!=", ">", "<", ">=", "<=", "contains")


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
    """Amostra de linhas de uma tabela (limit entre 1 e 50, offset >= 0)."""
    dataset = _get_dataset_or_raise(dataset_id)
    found = _find_table(dataset, table)

    safe_limit = max(1, min(limit, MAX_TOOL_ROWS))
    safe_offset = max(0, offset)

    rows = store.rows_by_table(dataset_id).get(found.id, [])
    page = rows[safe_offset : safe_offset + safe_limit]

    return {
        "table": found.name,
        "totalRows": len(rows),
        "returned": len(page),
        "rows": page,
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
    `value`. Devolve no máximo 50 linhas, mas informa o total de acertos."""
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

    return {
        "table": found_table.name,
        "column": column,
        "operator": operator,
        "value": value,
        "totalMatches": len(matches),
        "returned": len(matches[:MAX_TOOL_ROWS]),
        "rows": matches[:MAX_TOOL_ROWS],
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
