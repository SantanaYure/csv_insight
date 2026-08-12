import { Box, Table, Tbody, Td, Th, Thead, Tr } from '@chakra-ui/react';

import type { DatasetColumn } from '../../types/dataset';
import { formatCurrency } from '../../utils/formatCurrency';
import { formatDateTime } from '../../utils/formatDate';
import { formatNumber } from '../../utils/formatNumber';

interface DataPreviewProps {
  columns: DatasetColumn[];
  rows: Record<string, unknown>[];
  caption?: string;
}

/** Amostra das primeiras linhas da tabela, com scroll horizontal. */
export function DataPreview({ columns, rows, caption }: DataPreviewProps) {
  return (
    <Box
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
      borderRadius="xl"
      overflowX="auto"
    >
      <Table minW="680px" fontSize="13.5px" sx={{ borderCollapse: 'collapse' }}>
        {caption ? (
          <Box as="caption" srOnly>
            {caption}
          </Box>
        ) : null}
        <Thead>
          <Tr>
            {columns.map((column) => (
              <Th key={column.name} scope="col" whiteSpace="nowrap" fontFamily="mono" fontSize="12px" px="14px" py="10px">
                {column.name}
              </Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {rows.map((row, index) => (
            <Tr key={index}>
              {columns.map((column) => (
                <Td key={column.name} whiteSpace="nowrap" color="text.secondary" px="14px" py="10px">
                  {formatPreviewValue(row[column.name], column.dataType)}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}

/** Aplica ao valor bruto a formatação correspondente ao tipo da coluna. */
function formatPreviewValue(value: unknown, dataType: DatasetColumn['dataType']): string {
  if (value === null || value === undefined || value === '') return '—';

  if (typeof value === 'number') {
    return dataType === 'currency' ? formatCurrency(value) : formatNumber(value);
  }

  if (dataType === 'date') {
    const parsed = new Date(String(value));
    if (!Number.isNaN(parsed.getTime())) return formatDateTime(parsed);
  }

  return String(value);
}
