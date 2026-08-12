import { Box, Table, Tbody, Td, Th, Thead, Tr } from '@chakra-ui/react';

import type { DataDictionaryEntry } from '../../types/dataset';
import { formatDataType } from '../../utils/dataType';
import { TypeBadge } from './TypeBadge';

/** Tabela do dicionário de dados: tabela, coluna, tipo e descrição. */
export function DataDictionaryTable({ entries }: { entries: DataDictionaryEntry[] }) {
  return (
    <Box overflowX="auto">
      <Table minW="660px" fontSize="14px" sx={{ borderCollapse: 'collapse' }}>
        <Box as="caption" srOnly>
          Dicionário de dados do conjunto carregado
        </Box>
        <Thead>
          <Tr>
            <Th scope="col" px="22px">
              Tabela
            </Th>
            <Th scope="col">Coluna</Th>
            <Th scope="col">Tipo</Th>
            <Th scope="col" px="22px">
              Descrição
            </Th>
          </Tr>
        </Thead>
        <Tbody>
          {entries.map((entry) => (
            <Tr key={`${entry.table}.${entry.column}`}>
              <Td px="22px" fontFamily="mono" fontSize="13px" color="text.muted">
                {entry.table}
              </Td>
              <Td fontFamily="mono" fontSize="13.5px" fontWeight={500} color="text.primary">
                {entry.column}
              </Td>
              <Td>
                <TypeBadge>{formatDataType(entry.dataType)}</TypeBadge>
              </Td>
              <Td px="22px" color="text.secondary">
                {entry.description}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}
