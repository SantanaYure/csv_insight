import { Box, Heading, Text } from '@chakra-ui/react';

import type { TableQueryResult } from '../../types/query';
import { DataTable } from './DataTable';
import { highlightNumbers } from './highlightNumbers';

/** Resposta tabular com título opcional e moldura arredondada. */
export function TableResult({ result }: { result: TableQueryResult }) {
  return (
    <Box>
      {result.title ? (
        <Heading as="h3" m={0} fontSize="16px" fontWeight={600} color="text.primary">
          {result.title}
        </Heading>
      ) : null}

      {result.answer ? (
        <Text
          mt={result.title ? '8px' : 0}
          fontSize="15px"
          lineHeight={1.6}
          color={result.title ? 'text.muted' : 'text.primary'}
        >
          {highlightNumbers(result.answer)}
        </Text>
      ) : null}

      <Box mt={result.title || result.answer ? '14px' : 0}>
        {/* A legenda só é necessária quando não há título visível acima. */}
        <DataTable
          columns={result.columns}
          rows={result.rows}
          caption={result.title ? undefined : 'Resultado da consulta'}
        />
      </Box>
    </Box>
  );
}
