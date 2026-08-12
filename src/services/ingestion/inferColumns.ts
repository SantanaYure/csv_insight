import type { DatasetColumn, DatasetColumnType } from '../../types/dataset';
import type { DictionaryEntry } from './dataDictionary';
import { mapDictionaryType } from './dataDictionary';

export type CellValue = string | number | null;
export type DataRow = Record<string, CellValue>;

const ISO_DATE = /^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?/;
const BR_DATE = /^\d{2}\/\d{2}\/\d{4}/;
const CURRENCY_HINT = /(valor|preco|preço|total|tributo|custo|montante|desconto)/i;

/** Linhas por bloco antes de devolver o controle ao navegador. Mantém a aba
 * responsiva mesmo em tabelas com centenas de milhares de registros. */
const CHUNK_SIZE = 20_000;

function yieldToMain(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

/**
 * Monta as colunas da tabela combinando o dicionário de dados (quando existe)
 * com a inferência a partir dos próprios valores. Processa uma coluna por
 * vez, cedendo o controle ao navegador entre elas — cada coluna já é uma
 * varredura completa das linhas, então isso evita travar a aba em tabelas
 * com muitas colunas e muitos registros.
 */
export async function buildColumns(
  headers: string[],
  rows: Record<string, string>[],
  dictionary: Map<string, DictionaryEntry> | undefined,
): Promise<DatasetColumn[]> {
  const columns: DatasetColumn[] = [];

  for (const header of headers) {
    const entry = dictionary?.get(header);
    const declared = mapDictionaryType(entry);
    const dataType = declared ?? inferType(header, rows.map((row) => row[header] ?? ''));

    let nullCount = 0;
    for (const row of rows) {
      if (isBlank(row[header])) nullCount += 1;
    }

    columns.push({
      name: header,
      dataType,
      description: entry?.description?.trim() || undefined,
      nullable: nullCount > 0,
      nullCount,
    });

    await yieldToMain();
  }

  return columns;
}

/** Converte as linhas de texto para os tipos definidos nas colunas, em
 * blocos, para não bloquear a aba em tabelas grandes. */
export async function coerceRows(
  rows: Record<string, string>[],
  columns: DatasetColumn[],
): Promise<DataRow[]> {
  const coerced: DataRow[] = new Array(rows.length);

  for (let start = 0; start < rows.length; start += CHUNK_SIZE) {
    const end = Math.min(start + CHUNK_SIZE, rows.length);

    for (let i = start; i < end; i++) {
      const row = rows[i];
      const out: DataRow = {};
      columns.forEach((column) => {
        out[column.name] = coerceValue(row[column.name] ?? '', column.dataType);
      });
      coerced[i] = out;
    }

    await yieldToMain();
  }

  return coerced;
}

export function coerceValue(raw: string, dataType: DatasetColumnType): CellValue {
  const value = raw.trim();
  if (value === '') return null;

  if (dataType === 'number' || dataType === 'currency') {
    const parsed = parseNumber(value);
    return parsed === null ? value : parsed;
  }

  return value;
}

/**
 * Aceita `1234.56`, `1.234,56` e `1234,56`. Retorna `null` quando o texto não
 * é numérico.
 */
export function parseNumber(value: string): number | null {
  const cleaned = value.replace(/[R$\s ]/gi, '');
  if (cleaned === '' || !/[0-9]/.test(cleaned)) return null;

  const hasComma = cleaned.includes(',');
  const hasDot = cleaned.includes('.');

  let normalized = cleaned;
  if (hasComma && hasDot) {
    // O separador decimal é o último que aparece.
    normalized =
      cleaned.lastIndexOf(',') > cleaned.lastIndexOf('.')
        ? cleaned.replace(/\./g, '').replace(',', '.')
        : cleaned.replace(/,/g, '');
  } else if (hasComma) {
    normalized = cleaned.replace(',', '.');
  }

  if (!/^-?\d*\.?\d+$/.test(normalized)) return null;

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function inferType(header: string, values: string[]): DatasetColumnType {
  const samples = values.filter((value) => !isBlank(value)).slice(0, 200);
  if (samples.length === 0) return 'unknown';

  if (samples.every((value) => ISO_DATE.test(value) || BR_DATE.test(value))) return 'date';

  if (samples.every((value) => /^(true|false|sim|não|nao|0|1)$/i.test(value))) {
    // 0/1 são ambíguos: só tratamos como booleano quando há texto explícito.
    if (samples.some((value) => /^(true|false|sim|não|nao)$/i.test(value))) return 'boolean';
  }

  // Sequências longas de dígitos (chave de acesso, CNPJ sem máscara, códigos)
  // são identificadores, não números — converter perderia precisão.
  const looksLikeIdentifier = samples.some((value) => /^\d{16,}$/.test(value.trim()));

  if (!looksLikeIdentifier && samples.every((value) => parseNumber(value) !== null)) {
    return CURRENCY_HINT.test(header) ? 'currency' : 'number';
  }

  return 'string';
}

function isBlank(value: string | undefined): boolean {
  return value === undefined || value.trim() === '';
}
