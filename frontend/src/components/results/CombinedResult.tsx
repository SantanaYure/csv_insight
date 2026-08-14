import { Box, Grid, Text } from '@chakra-ui/react';

import type { CombinedQueryResult } from '../../types/query';
import { ChartResultFromSpec } from './ChartResult';
import { DataTable } from './DataTable';
import { highlightNumbers } from './highlightNumbers';

/**
 * Resposta combinada: texto no topo e, abaixo, tabela e gráfico lado a lado
 * no desktop e empilhados no mobile.
 */
export function CombinedResult({ result }: { result: CombinedQueryResult }) {
  const hasTable = Boolean(result.table);
  const hasChart = Boolean(result.chart);

  return (
    <Box>
      <Text m={0} fontSize="15.5px" lineHeight={1.65} color="text.primary">
        {highlightNumbers(result.answer)}
      </Text>

      {hasTable || hasChart ? (
        <Grid
          mt="18px"
          gap="16px"
          templateColumns={
            hasTable && hasChart
              ? { base: '1fr', md: 'repeat(2, minmax(0, 1fr))' }
              : '1fr'
          }
        >
          {result.table ? (
            <DataTable
              columns={result.table.columns}
              rows={result.table.rows}
              minWidth="230px"
              fontSize="14px"
              highlightFirstRow
              caption={result.table.title ?? 'Resultado da consulta'}
            />
          ) : null}

          {result.chart ? (
            <Box
              p="16px"
              borderWidth="1px"
              borderStyle="solid"
              borderColor="border.default"
              borderRadius="xl"
            >
              <ChartResultFromSpec chart={result.chart.chart} height={210} hideTitle />
            </Box>
          ) : null}
        </Grid>
      ) : null}
    </Box>
  );
}
