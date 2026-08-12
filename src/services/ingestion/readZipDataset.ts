import { unzip } from 'fflate';

import type { Dataset, DatasetTable } from '../../types/dataset';
import { generateId } from '../../utils/generateId';
import { buildDataDictionary, isDictionaryFile, normalizeFileName } from './dataDictionary';
import type { DataDictionary } from './dataDictionary';
import { decodeCsvBytes } from './decodeText';
import { buildColumns, coerceRows } from './inferColumns';
import type { DataRow } from './inferColumns';
import { parseCsv } from './parseCsv';

/** Erro de ingestão com mensagem pronta para exibição. */
export class DatasetIngestionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DatasetIngestionError';
  }
}

export interface IngestedDataset {
  dataset: Dataset;
  /** Linhas completas de cada tabela, indexadas pelo id da tabela. */
  rows: Record<string, DataRow[]>;
}

/** Progresso reportado enquanto cada arquivo do ZIP é processado. */
export interface IngestionProgress {
  fileName: string;
  rowCount: number;
  tableIndex: number;
  tableCount: number;
}

const PREVIEW_ROWS = 5;
const MAX_CSV_FILES = 40;

/**
 * Lê o ZIP enviado, interpreta os CSVs e monta o `Dataset` da aplicação.
 * O arquivo de dicionário, quando presente, define tipos e descrições das
 * colunas; as demais planilhas viram tabelas consultáveis.
 *
 * Todo o trabalho pesado (parse do CSV, inferência de tipos, conversão de
 * valores) é assíncrono e cede o controle ao navegador periodicamente, para
 * que arquivos grandes (centenas de milhares de linhas) não travem a aba.
 */
export async function readZipDataset(
  file: File,
  onProgress?: (progress: IngestionProgress) => void,
): Promise<IngestedDataset> {
  const files = await unzipFile(file);
  const csvEntries = Object.entries(files).filter(([name]) => isUsableCsv(name));

  if (csvEntries.length === 0) {
    throw new DatasetIngestionError(
      'Nenhum arquivo .csv foi encontrado dentro do ZIP. Verifique o conteúdo do pacote e envie novamente.',
    );
  }

  if (csvEntries.length > MAX_CSV_FILES) {
    throw new DatasetIngestionError(
      `O ZIP contém ${csvEntries.length} arquivos CSV. O limite por conjunto de dados é de ${MAX_CSV_FILES}.`,
    );
  }

  const dictionaryEntry = csvEntries.find(([name]) => isDictionaryFile(baseName(name)));
  const dictionary: DataDictionary = dictionaryEntry
    ? buildDataDictionary(await parseCsv(decodeCsvBytes(dictionaryEntry[1])))
    : { entries: new Map(), rowCount: 0 };

  const tableEntries = csvEntries.filter(([name]) => !isDictionaryFile(baseName(name)));

  if (tableEntries.length === 0) {
    throw new DatasetIngestionError(
      'O ZIP contém apenas o dicionário de dados. Inclua ao menos um arquivo CSV com registros.',
    );
  }

  const tables: DatasetTable[] = [];
  const rows: Record<string, DataRow[]> = {};

  for (const [tableIndex, [name, bytes]] of tableEntries.entries()) {
    const fileName = baseName(name);
    const csv = await parseCsv(decodeCsvBytes(bytes));

    if (csv.headers.length === 0) continue;

    const columns = await buildColumns(
      csv.headers,
      csv.rows,
      dictionary.entries.get(normalizeFileName(fileName)),
    );
    const coerced = await coerceRows(csv.rows, columns);
    const id = toTableId(fileName);

    tables.push({
      id,
      name: id,
      fileName,
      description: describeTable(columns.map((column) => column.name)),
      rowCount: coerced.length,
      columnCount: columns.length,
      columns,
      preview: coerced.slice(0, PREVIEW_ROWS),
    });

    rows[id] = coerced;

    onProgress?.({
      fileName,
      rowCount: coerced.length,
      tableIndex: tableIndex + 1,
      tableCount: tableEntries.length,
    });
  }

  if (tables.length === 0) {
    throw new DatasetIngestionError(
      'Não foi possível ler nenhuma tabela: os arquivos CSV estão vazios ou sem cabeçalho.',
    );
  }

  tables.sort((a, b) => b.rowCount - a.rowCount);

  const dataset: Dataset = {
    id: generateId('ds'),
    name: datasetNameFromFile(file.name),
    uploadedAt: new Date().toISOString(),
    status: 'ready',
    totalRows: tables.reduce((total, table) => total + table.rowCount, 0),
    totalColumns: tables.reduce((total, table) => total + table.columnCount, 0),
    tables,
    sourceFileName: file.name,
    sourceFileSize: file.size,
    dictionaryFileName: dictionaryEntry ? baseName(dictionaryEntry[0]) : undefined,
    summary: buildSummary(tables, dictionary),
  };

  return { dataset, rows };
}

function unzipFile(file: File): Promise<Record<string, Uint8Array>> {
  return file.arrayBuffer().then(
    (buffer) =>
      new Promise<Record<string, Uint8Array>>((resolve, reject) => {
        unzip(new Uint8Array(buffer), (error, result) => {
          if (error) {
            reject(
              new DatasetIngestionError(
                'Não foi possível abrir o arquivo. Confirme que ele é um .zip válido e não está protegido por senha.',
              ),
            );
            return;
          }
          resolve(result);
        });
      }),
  );
}

/** Ignora diretórios, metadados do macOS e arquivos que não sejam CSV. */
function isUsableCsv(path: string): boolean {
  if (path.endsWith('/')) return false;
  const name = baseName(path);
  if (name.startsWith('.') || path.startsWith('__MACOSX/')) return false;
  return name.toLowerCase().endsWith('.csv');
}

function baseName(path: string): string {
  return path.replace(/\\/g, '/').split('/').pop() ?? path;
}

function toTableId(fileName: string): string {
  return fileName.replace(/\.csv$/i, '').trim() || 'tabela';
}

function datasetNameFromFile(fileName: string): string {
  const base = fileName.replace(/\.zip$/i, '').replace(/[_-]+/g, ' ').trim();
  if (!base) return 'Conjunto de dados';
  return base.charAt(0).toUpperCase() + base.slice(1);
}

function describeTable(columnNames: string[]): string {
  const preview = columnNames.slice(0, 4).join(', ');
  const rest = columnNames.length - 4;
  return rest > 0 ? `${preview} e mais ${rest} colunas.` : `${preview}.`;
}

function buildSummary(tables: DatasetTable[], dictionary: DataDictionary): string {
  const tableList = tables.map((table) => table.name).join(', ');
  const totalColumns = tables.reduce((total, table) => total + table.columnCount, 0);
  const dictionaryNote = dictionary.rowCount
    ? ` O dicionário de dados descreve ${dictionary.rowCount} colunas.`
    : ' Nenhum dicionário de dados foi encontrado: os tipos foram inferidos a partir dos valores.';

  return `Foram lidas ${tables.length} tabelas (${tableList}), somando ${totalColumns} colunas.${dictionaryNote}`;
}
