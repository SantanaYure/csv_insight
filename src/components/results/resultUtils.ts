import type { QueryResult, TableColumnSpec, TableQueryResult } from '../../types/query';
import { formatCurrency } from '../../utils/formatCurrency';
import { formatNumber } from '../../utils/formatNumber';

/** Formata uma célula conforme o tipo declarado na coluna. */
export function formatCell(
  value: string | number | null | undefined,
  dataType?: TableColumnSpec['dataType'],
): string {
  if (value === null || value === undefined || value === '') return '—';

  if (typeof value === 'number') {
    if (dataType === 'currency') return formatCurrency(value);
    return formatNumber(value);
  }

  return String(value);
}

type TableLike = Pick<TableQueryResult, 'columns' | 'rows'>;

/** Serializa uma tabela de resultado em CSV com separador `;`. */
export function tableToCsv(table: TableLike): string {
  const header = table.columns.map((column) => escapeCsv(column.label)).join(';');
  const body = table.rows.map((row) =>
    table.columns.map((column) => escapeCsv(formatCell(row[column.key], column.dataType))).join(';'),
  );
  return [header, ...body].join('\n');
}

function escapeCsv(value: string): string {
  return /[";\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

/** Texto plano de uma resposta, usado pelo botão de copiar. */
export function resultToPlainText(result: QueryResult): string {
  switch (result.type) {
    case 'text':
      return [result.answer, result.detail].filter(Boolean).join('\n');
    case 'table':
      return [result.answer, result.title, tableToCsv(result)].filter(Boolean).join('\n');
    case 'chart':
      return [result.answer, result.chart.title, chartToText(result.chart.data, result.chart.xKey, result.chart.yKey)]
        .filter(Boolean)
        .join('\n');
    case 'combined':
      return [
        result.answer,
        result.table ? tableToCsv(result.table) : '',
        result.chart
          ? chartToText(result.chart.chart.data, result.chart.chart.xKey, result.chart.chart.yKey)
          : '',
      ]
        .filter(Boolean)
        .join('\n');
    case 'error':
      return [result.title, result.message, result.suggestion].filter(Boolean).join('\n');
    default:
      return '';
  }
}

function chartToText(
  data: Record<string, string | number>[],
  xKey: string,
  yKey: string,
): string {
  return data.map((point) => `${String(point[xKey])};${String(point[yKey])}`).join('\n');
}

/** Resumo curto usado nos cards do histórico. */
export function summarizeResult(result: QueryResult): string {
  switch (result.type) {
    case 'text':
      return result.answer;
    case 'table':
      return (
        result.answer ??
        `${result.rows.length} ${result.rows.length === 1 ? 'linha' : 'linhas'} · ${result.title ?? 'resultado tabular'}.`
      );
    case 'chart':
      return result.answer ?? `${result.chart.title} · ${result.chart.data.length} pontos.`;
    case 'combined':
      return result.answer;
    case 'error':
      return result.message;
    default:
      return '';
  }
}
