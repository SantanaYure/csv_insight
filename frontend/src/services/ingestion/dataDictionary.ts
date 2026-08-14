import type { DatasetColumnType } from '../../types/dataset';
import type { ParsedCsv } from './parseCsv';

/** Uma linha do `dicionario_dados.csv`. */
export interface DictionaryEntry {
  file: string;
  column: string;
  type: string;
  description: string;
  key: string;
  reference: string;
  format: string;
}

export interface DataDictionary {
  /** Indexado por `arquivo.csv` → nome da coluna. */
  entries: Map<string, Map<string, DictionaryEntry>>;
  rowCount: number;
}

/** Nomes aceitos para o arquivo de dicionário dentro do ZIP. */
export function isDictionaryFile(fileName: string): boolean {
  const base = fileName.toLowerCase();
  return base.includes('dicionario') || base.includes('dictionary');
}

/**
 * Interpreta o dicionário de dados. Os cabeçalhos esperados são
 * `arquivo, coluna, tipo, descricao, chave, referencia, formato`, mas as
 * variações mais comuns (com acento ou em inglês) também são aceitas.
 */
export function buildDataDictionary(csv: ParsedCsv): DataDictionary {
  const pick = createHeaderPicker(csv.headers);

  const fileKey = pick(['arquivo', 'tabela', 'file', 'table']);
  const columnKey = pick(['coluna', 'campo', 'column', 'field']);
  const typeKey = pick(['tipo', 'type']);
  const descriptionKey = pick(['descricao', 'descrição', 'description']);
  const keyKey = pick(['chave', 'key']);
  const referenceKey = pick(['referencia', 'referência', 'reference']);
  const formatKey = pick(['formato', 'format']);

  const entries = new Map<string, Map<string, DictionaryEntry>>();
  let rowCount = 0;

  if (!fileKey || !columnKey) {
    return { entries, rowCount };
  }

  csv.rows.forEach((row) => {
    const file = normalizeFileName(row[fileKey] ?? '');
    const column = (row[columnKey] ?? '').trim();
    if (!file || !column) return;

    const entry: DictionaryEntry = {
      file,
      column,
      type: typeKey ? (row[typeKey] ?? '') : '',
      description: descriptionKey ? (row[descriptionKey] ?? '') : '',
      key: keyKey ? (row[keyKey] ?? '') : '',
      reference: referenceKey ? (row[referenceKey] ?? '') : '',
      format: formatKey ? (row[formatKey] ?? '') : '',
    };

    if (!entries.has(file)) entries.set(file, new Map());
    entries.get(file)?.set(column, entry);
    rowCount += 1;
  });

  return { entries, rowCount };
}

/** Converte o tipo declarado no dicionário para o modelo da aplicação. */
export function mapDictionaryType(entry: DictionaryEntry | undefined): DatasetColumnType | null {
  if (!entry) return null;

  const type = entry.type.trim().toLowerCase();
  const format = entry.format.trim().toLowerCase();

  if (format === 'brl' || format === 'currency' || type === 'currency' || type === 'money') {
    return 'currency';
  }

  if (['datetime', 'date', 'timestamp', 'data'].includes(type)) return 'date';
  if (['integer', 'int', 'inteiro', 'long'].includes(type)) return 'number';
  if (['decimal', 'float', 'double', 'number', 'numeric'].includes(type)) return 'number';
  if (['boolean', 'bool', 'booleano'].includes(type)) return 'boolean';
  if (['string', 'text', 'texto', 'varchar'].includes(type)) return 'string';

  return null;
}

/** `notas_fiscais.csv`, `./NFs/notas_fiscais.CSV` → `notas_fiscais.csv`. */
export function normalizeFileName(value: string): string {
  const withoutPath = value.trim().replace(/\\/g, '/').split('/').pop() ?? '';
  return withoutPath.toLowerCase();
}

function createHeaderPicker(headers: string[]) {
  const normalized = new Map(headers.map((header) => [deburr(header), header]));

  return (candidates: string[]): string | null => {
    for (const candidate of candidates) {
      const match = normalized.get(deburr(candidate));
      if (match) return match;
    }
    return null;
  };
}

function deburr(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}
