import { Box, Table, Tbody, Td, Th, Thead, Tr } from '@chakra-ui/react';

import type { TableColumnSpec } from '../../types/query';
import { formatCell } from './resultUtils';

interface DataTableProps {
  columns: TableColumnSpec[];
  rows: Record<string, string | number | null>[];
  /** Largura mínima antes de ativar o scroll horizontal. */
  minWidth?: string;
  fontSize?: string;
  /** Destaca a primeira linha, como no resultado combinado do design. */
  highlightFirstRow?: boolean;
  caption?: string;
}

/** Tabela com moldura arredondada e scroll horizontal no mobile. */
export function DataTable({
  columns,
  rows,
  minWidth = '340px',
  fontSize = '14.5px',
  highlightFirstRow = false,
  caption,
}: DataTableProps) {
  return (
    <Box
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
      borderRadius="xl"
      overflowX="auto"
    >
      <Table minW={minWidth} fontSize={fontSize} sx={{ borderCollapse: 'collapse' }}>
        {caption ? (
          <Box as="caption" srOnly>
            {caption}
          </Box>
        ) : null}
        <Thead>
          <Tr>
            {columns.map((column) => (
              <Th
                key={column.key}
                scope="col"
                textAlign={column.align ?? (column.dataType === 'number' || column.dataType === 'currency' ? 'right' : 'left')}
                px="16px"
              >
                {column.label}
              </Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {rows.map((row, rowIndex) => (
            <Tr key={`${String(row[columns[0]?.key ?? 'row'])}-${rowIndex}`}>
              {columns.map((column, columnIndex) => {
                const isValueColumn = columnIndex > 0;
                const emphasized = highlightFirstRow ? rowIndex === 0 : true;
                return (
                  <Td
                    key={column.key}
                    px="16px"
                    textAlign={column.align ?? (column.dataType === 'number' || column.dataType === 'currency' ? 'right' : 'left')}
                    fontWeight={isValueColumn && emphasized ? 600 : 400}
                    color={isValueColumn && !emphasized ? 'text.secondary' : 'text.primary'}
                  >
                    {formatCell(row[column.key], column.dataType)}
                  </Td>
                );
              })}
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}
