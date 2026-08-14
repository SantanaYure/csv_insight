export type ChartType = 'bar' | 'line' | 'pie' | 'area';

export interface ChartSpec {
  type: ChartType;
  title: string;
  xKey: string;
  yKey: string;
  data: Record<string, string | number>[];
  /** Rótulo do eixo Y usado no tooltip e na legenda. */
  yLabel?: string;
  /** Formatação aplicada aos valores do eixo Y. */
  valueFormat?: 'number' | 'currency';
  /** Chave do item destacado (o design realça o mês de maior volume). */
  highlightKey?: string;
  caption?: string;
}

export interface TableColumnSpec {
  key: string;
  label: string;
  dataType?: 'string' | 'number' | 'currency' | 'date';
  align?: 'left' | 'right';
}

export interface TextQueryResult {
  type: 'text';
  answer: string;
  /** Linha complementar exibida abaixo da resposta. */
  detail?: string;
}

export interface TableQueryResult {
  type: 'table';
  answer?: string;
  title?: string;
  columns: TableColumnSpec[];
  rows: Record<string, string | number | null>[];
}

export interface ChartQueryResult {
  type: 'chart';
  answer?: string;
  chart: ChartSpec;
}

export interface CombinedQueryResult {
  type: 'combined';
  answer: string;
  table?: Omit<TableQueryResult, 'type'>;
  chart?: Omit<ChartQueryResult, 'type'>;
}

export interface ErrorQueryResult {
  type: 'error';
  title: string;
  message: string;
  suggestion?: string;
}

export type QueryResult =
  | TextQueryResult
  | TableQueryResult
  | ChartQueryResult
  | CombinedQueryResult
  | ErrorQueryResult;

export type QueryResultType = QueryResult['type'];

/** Rótulos em português usados nos badges de histórico e nos filtros. */
export const QUERY_RESULT_LABEL: Record<QueryResultType, string> = {
  text: 'Texto',
  table: 'Tabela',
  chart: 'Gráfico',
  combined: 'Combinado',
  error: 'Erro',
};
