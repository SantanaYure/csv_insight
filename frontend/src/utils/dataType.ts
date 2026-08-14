import type { DatasetColumnType } from '../types/dataset';

const LABELS: Record<DatasetColumnType, string> = {
  string: 'texto',
  number: 'número',
  date: 'data',
  boolean: 'booleano',
  currency: 'moeda',
  unknown: 'desconhecido',
};

/** Rótulo em português exibido no badge de tipo das colunas. */
export function formatDataType(dataType: DatasetColumnType): string {
  return LABELS[dataType];
}
