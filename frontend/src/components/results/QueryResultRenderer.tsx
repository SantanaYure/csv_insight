import { Box } from '@chakra-ui/react';

import type { QueryResult } from '../../types/query';
import { ChartResultFromSpec } from './ChartResult';
import { CombinedResult } from './CombinedResult';
import { ErrorResult } from './ErrorResult';
import { ResultFooter } from './ResultFooter';
import { TableResult } from './TableResult';
import { TextResult } from './TextResult';
import { resultToPlainText, tableToCsv } from './resultUtils';

interface QueryResultRendererProps {
  result: QueryResult;
  /** Duração da consulta, exibida no rodapé. */
  durationMs?: number;
  onRetry?: () => void;
}

const CHART_LABEL: Record<string, string> = {
  bar: 'barras',
  line: 'linhas',
  area: 'área',
  pie: 'pizza',
};

/** Escolhe o componente adequado para cada tipo de resultado. */
export function QueryResultRenderer({ result, durationMs, onRetry }: QueryResultRendererProps) {
  return (
    <Box>
      {renderBody()}
      <ResultFooter
        label={footerLabel()}
        copyText={resultToPlainText(result)}
        csv={csvPayload()}
        onRetry={onRetry}
      />
    </Box>
  );

  function renderBody() {
    switch (result.type) {
      case 'text':
        return <TextResult result={result} />;
      case 'table':
        return <TableResult result={result} />;
      case 'chart':
        return <ChartResultFromSpec chart={result.chart} />;
      case 'combined':
        return <CombinedResult result={result} />;
      case 'error':
        return <ErrorResult result={result} />;
      default:
        return null;
    }
  }

  function footerLabel(): string {
    const seconds = durationMs ? `${(durationMs / 1000).toFixed(1).replace('.', ',')} s` : null;

    switch (result.type) {
      case 'text':
        return ['Resposta em texto', seconds].filter(Boolean).join(' · ');
      case 'table':
        return `Resposta em tabela · ${result.rows.length} ${result.rows.length === 1 ? 'linha' : 'linhas'}`;
      case 'chart':
        return `Resposta em gráfico · ${CHART_LABEL[result.chart.type] ?? result.chart.type}`;
      case 'combined':
        return 'Resposta combinada · texto, tabela e gráfico';
      case 'error':
        return 'Sem resultado';
      default:
        return '';
    }
  }

  function csvPayload() {
    if (result.type === 'table') {
      return { fileName: 'resultado.csv', content: tableToCsv(result) };
    }
    if (result.type === 'combined' && result.table) {
      return { fileName: 'resultado.csv', content: tableToCsv(result.table) };
    }
    return undefined;
  }
}
