import { Box, Table, Tbody, Td, Th, Thead, Tr } from '@chakra-ui/react';

import type { DatasetColumn } from '../../types/dataset';
import { formatDataType } from '../../utils/dataType';
import { formatNumber } from '../../utils/formatNumber';
import { TypeBadge } from './TypeBadge';

/** Tabela de colunas: nome, tipo, descrição e nulos. */
export function ColumnList({ columns, caption }: { columns: DatasetColumn[]; caption?: string }) {
  return (
    <Box
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
      borderRadius="xl"
      overflowX="auto"
    >
      <Table minW="620px" fontSize="14px" sx={{ borderCollapse: 'collapse' }}>
        {caption ? (
          <Box as="caption" srOnly>
            {caption}
          </Box>
        ) : null}
        <Thead>
          <Tr>
            <Th scope="col">Coluna</Th>
            <Th scope="col">Tipo</Th>
            <Th scope="col">Descrição</Th>
            <Th scope="col" textAlign="right">
              Nulos
            </Th>
          </Tr>
        </Thead>
        <Tbody>
          {columns.map((column) => (
            <Tr key={column.name}>
              <Td fontFamily="mono" fontSize="13.5px" fontWeight={500} color="text.primary">
                {column.label ?? column.name}
              </Td>
              <Td>
                <TypeBadge>{formatDataType(column.dataType)}</TypeBadge>
              </Td>
              <Td color="text.secondary">{column.description ?? '—'}</Td>
              <Td textAlign="right" color="text.muted">
                {column.nullCount !== undefined
                  ? formatNumber(column.nullCount)
                  : column.nullable
                    ? 'permite'
                    : '0'}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}
