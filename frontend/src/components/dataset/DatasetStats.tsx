import { Box, Flex, Grid, Text } from '@chakra-ui/react';
import { Check } from 'lucide-react';

import type { Dataset } from '../../types/dataset';
import { formatNumber } from '../../utils/formatNumber';
import { SurfaceCard } from '../common/SurfaceCard';

/** Grade com os quatro indicadores do dataset. */
export function DatasetStats({ dataset }: { dataset: Dataset }) {
  const tableNames = dataset.tables
    .map((table) => table.name.replace(/_.*$/, ''))
    .join(', ');

  return (
    <Grid
      templateColumns={{
        base: '1fr',
        sm: 'repeat(2, minmax(0, 1fr))',
        lg: 'repeat(4, minmax(0, 1fr))',
      }}
      gap="16px"
      mt="32px"
    >
      <StatCard
        label="Arquivos CSV"
        value={String(dataset.tables.length)}
        hint={tableNames}
      />
      <StatCard
        label="Registros"
        value={formatNumber(dataset.totalRows)}
        hint={`somando as ${dataset.tables.length} tabelas`}
      />
      <StatCard
        label="Colunas"
        value={String(dataset.totalColumns)}
        hint={
          dataset.dictionaryFileName
            ? 'descritas no dicionário'
            : 'com tipos inferidos dos valores'
        }
      />
      <StatusCard status={dataset.status} />
    </Grid>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <SurfaceCard p="20px">
      <Text m={0} fontSize="12px" fontWeight={600} letterSpacing="0.08em" textTransform="uppercase" color="text.muted">
        {label}
      </Text>
      <Text mt="10px" fontSize="32px" fontWeight={700} letterSpacing="-0.02em" color="text.primary" lineHeight={1.1}>
        {value}
      </Text>
      <Text mt="4px" fontSize="13.5px" color="text.muted">
        {hint}
      </Text>
    </SurfaceCard>
  );
}

function StatusCard({ status }: { status: Dataset['status'] }) {
  const label =
    status === 'ready' ? 'Processado' : status === 'processing' ? 'Processando' : 'Com erro';
  const hint =
    status === 'ready'
      ? 'Nenhum erro encontrado'
      : status === 'processing'
        ? 'Preparando o ambiente de consulta'
        : 'Revise o arquivo enviado';

  return (
    <SurfaceCard tone="soft" p="20px">
      <Text m={0} fontSize="12px" fontWeight={600} letterSpacing="0.08em" textTransform="uppercase" color="text.secondary">
        Status
      </Text>
      <Flex align="center" gap="9px" mt="10px">
        <Box
          as="span"
          aria-hidden="true"
          display="grid"
          placeItems="center"
          width="28px"
          height="28px"
          borderRadius="full"
          bg="brand.primary"
          color="#111111"
          flex="none"
        >
          <Check size={16} strokeWidth={2.6} />
        </Box>
        <Text m={0} fontSize="17px" fontWeight={600} color="text.primary">
          {label}
        </Text>
      </Flex>
      <Text mt="8px" fontSize="13.5px" color="text.secondary">
        {hint}
      </Text>
    </SurfaceCard>
  );
}
