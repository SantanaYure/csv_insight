export type DatasetStatus = 'processing' | 'ready' | 'error';

export type DatasetColumnType =
  | 'string'
  | 'number'
  | 'date'
  | 'boolean'
  | 'currency'
  | 'unknown';

export interface DatasetColumn {
  name: string;
  label?: string;
  dataType: DatasetColumnType;
  description?: string;
  nullable: boolean;
  /**
   * Quantidade de valores nulos encontrados na coluna. Opcional porque o
   * backend pode não calcular a estatística; o design exibe esse número na
   * coluna "Nulos" da tabela de colunas.
   */
  nullCount?: number;
}

export interface DatasetTable {
  id: string;
  name: string;
  fileName: string;
  description?: string;
  rowCount: number;
  columnCount: number;
  columns: DatasetColumn[];
  preview: Record<string, unknown>[];
}

export interface Dataset {
  id: string;
  name: string;
  uploadedAt: string;
  status: DatasetStatus;
  totalRows: number;
  totalColumns: number;
  tables: DatasetTable[];
  /** Metadados do arquivo enviado, exibidos no resumo. */
  sourceFileName?: string;
  sourceFileSize?: number;
  dictionaryFileName?: string;
  summary?: string;
}

/** Linha do dicionário de dados exibida na aba "Dicionário de dados". */
export interface DataDictionaryEntry {
  table: string;
  column: string;
  dataType: DatasetColumnType;
  description: string;
}

/** Etapas do processamento exibidas após o upload. */
export type ProcessingStepStatus = 'pending' | 'running' | 'done' | 'error';

export interface ProcessingStep {
  id: string;
  label: string;
  status: ProcessingStepStatus;
  detail?: string;
}
