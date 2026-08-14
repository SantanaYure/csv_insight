import { Box, Flex, Heading, Text } from '@chakra-ui/react';
import { useMemo } from 'react';

import { SurfaceCard } from '../common/SurfaceCard';
import { DataDictionaryTable } from '../dataset/DataDictionaryTable';
import { DatasetStats } from '../dataset/DatasetStats';
import { TableAccordion } from '../dataset/TableAccordion';
import { pageGutter } from '../../theme';
import type { Dataset, DataDictionaryEntry } from '../../types/dataset';
import { formatDateTime } from '../../utils/formatDate';
import { formatFileSize } from '../../utils/formatFileSize';

interface DataPanelProps {
  dataset: Dataset;
  selectedTableId: string | null;
  onSelectTable: (tableId: string | null) => void;
}

/** Painel "Dados": estatísticas, tabelas (em acordeão) e dicionário de dados. */
export function DataPanel({ dataset, selectedTableId, onSelectTable }: DataPanelProps) {
  const dictionary = useMemo<DataDictionaryEntry[]>(
    () =>
      dataset.tables.flatMap((table) =>
        table.columns.map((column) => ({
          table: table.name,
          column: column.name,
          dataType: column.dataType,
          description: column.description ?? '',
        })),
      ),
    [dataset.tables],
  );

  return (
    <Box px={pageGutter} pt="24px" pb="56px" maxW="1180px" mx="auto" width="100%">
      <DatasetStats dataset={dataset} />

      <SurfaceCard mt="24px" px={{ base: '18px', md: '24px' }} py="22px" elevated={false}>
        <Heading as="h2" m={0} fontSize="16px" fontWeight={600}>
          Resumo dos arquivos
        </Heading>
        <Text mt="10px" maxW="70ch" fontSize="14.5px" lineHeight={1.65} color="text.muted">
          {dataset.summary}
        </Text>

        <Flex
          gap="24px"
          wrap="wrap"
          mt="18px"
          pt="18px"
          borderTopWidth="1px"
          borderTopStyle="solid"
          borderColor="border.default"
        >
          <SummaryField label="Upload" value={formatDateTime(dataset.uploadedAt)} />
          <SummaryField
            label="Arquivo"
            value={`${dataset.sourceFileName} · ${formatFileSize(dataset.sourceFileSize ?? 0)}`}
          />
          <SummaryField
            label="Dicionário"
            value={dataset.dictionaryFileName ?? 'Não incluído no ZIP'}
          />
        </Flex>
      </SurfaceCard>

      <Heading as="h2" size="subtitle" mt="32px" mb="14px">
        Tabelas
      </Heading>
      <TableAccordion
        tables={dataset.tables}
        expandedTable={selectedTableId}
        onToggle={onSelectTable}
      />

      <Heading as="h2" size="subtitle" mt="36px" mb="14px">
        Dicionário de dados
      </Heading>
      <SurfaceCard overflow="hidden">
        <Box
          px={{ base: '18px', md: '22px' }}
          py="18px"
          borderBottomWidth="1px"
          borderBottomStyle="solid"
          borderColor="border.default"
        >
          <Text m={0} fontSize="14px" fontWeight={600} color="text.primary">
            {dataset.dictionaryFileName ?? 'Colunas identificadas'}
          </Text>
          <Text mt="4px" fontSize="13px" color="text.muted">
            {dataset.totalColumns} colunas
            {dataset.dictionaryFileName
              ? ' descritas no dicionário de dados'
              : ' · tipos inferidos a partir dos valores (nenhum dicionário no ZIP)'}
          </Text>
        </Box>
        <DataDictionaryTable entries={dictionary} />
      </SurfaceCard>
    </Box>
  );
}

function SummaryField({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Text m={0} fontSize="11.5px" letterSpacing="0.06em" textTransform="uppercase" color="text.muted">
        {label}
      </Text>
      <Text mt="4px" fontSize="14px" fontWeight={500} color="text.primary">
        {value}
      </Text>
    </Box>
  );
}
