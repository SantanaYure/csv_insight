import { Box, Flex, Text } from '@chakra-ui/react';
import type { ReactNode } from 'react';

import type { Dataset } from '../../types/dataset';
import { formatNumber } from '../../utils/formatNumber';
import { StatusBadge } from './StatusBadge';

const STATUS_LABEL: Record<Dataset['status'], string> = {
  ready: 'Dataset pronto',
  processing: 'Processando',
  error: 'Falha no processamento',
};

/** Cartão amarelo-claro com o nome do dataset, status e contagens. */
export function SidebarDatasetCard({
  dataset,
  compact = false,
}: {
  dataset: Dataset;
  compact?: boolean;
}) {
  return (
    <Box
      p={compact ? '14px' : '16px'}
      borderRadius="xl"
      bg="brand.tint"
      borderWidth="1px"
      borderStyle="solid"
      borderColor="brand.soft"
    >
      <Text m={0} fontSize={compact ? '14.5px' : '15px'} fontWeight={600} color="text.primary">
        {dataset.name}
      </Text>

      {compact ? (
        <Text mt="6px" fontSize="12.5px" color="text.muted">
          {dataset.tables.length} tabelas · {formatNumber(dataset.totalRows)} registros
        </Text>
      ) : (
        <>
          <StatusBadge
            tone={dataset.status === 'ready' ? 'brand' : 'neutral'}
            withDot
            mt="10px"
            height="24px"
            px="9px"
            fontSize="11.5px"
          >
            {STATUS_LABEL[dataset.status]}
          </StatusBadge>
          <Flex gap="18px" mt="14px">
            <SidebarStat value={String(dataset.tables.length)} label="tabelas" />
            <SidebarStat value={formatNumber(dataset.totalRows)} label="registros" />
          </Flex>
        </>
      )}
    </Box>
  );
}

function SidebarStat({ value, label }: { value: string; label: string }) {
  return (
    <Box>
      <Text m={0} fontSize="17px" fontWeight={700} color="text.primary">
        {value}
      </Text>
      <Text mt="2px" fontSize="12px" color="text.muted">
        {label}
      </Text>
    </Box>
  );
}

export function SidebarGroupLabel({ children, ...rest }: { children: ReactNode; ml?: string }) {
  return (
    <Text m={0} mb="6px" ml="10px" textStyle="overline" color="text.muted" {...rest}>
      {children}
    </Text>
  );
}

/** Lista das tabelas do dataset: atalho para abri-las no painel "Dados". */
export function SidebarTableList({
  dataset,
  onSelectTable,
  compact = false,
}: {
  dataset: Dataset;
  onSelectTable: (tableId: string) => void;
  compact?: boolean;
}) {
  return (
    <Flex direction="column" gap="2px">
      {dataset.tables.map((table) => (
        <Flex
          key={table.id}
          as="button"
          type="button"
          onClick={() => onSelectTable(table.id)}
          align="center"
          gap="10px"
          minH={compact ? '40px' : '38px'}
          px={compact ? '12px' : '10px'}
          border={0}
          borderRadius="9px"
          bg="transparent"
          color="text.secondary"
          fontSize="14px"
          textAlign="left"
          cursor="pointer"
          _hover={{ bg: 'background.subtle' }}
        >
          <Box as="span" flex="none" width="6px" height="6px" borderRadius="2px" bg="brand.primary" />
          <Text as="span" flex="1" noOfLines={1} textAlign="left">
            {table.name}
          </Text>
          {!compact ? (
            <Text as="span" fontSize="12px" color="text.muted">
              {formatNumber(table.rowCount)}
            </Text>
          ) : null}
        </Flex>
      ))}
    </Flex>
  );
}

/** Lista de perguntas sugeridas exibida na sidebar; sempre leva à Consulta. */
export function SidebarSuggestions({
  questions,
  onSelect,
}: {
  questions: string[];
  onSelect: (question: string) => void;
}) {
  return (
    <Box>
      <SidebarGroupLabel>Perguntas sugeridas</SidebarGroupLabel>
      <Flex direction="column" gap="6px">
        {questions.map((question) => (
          <Box
            key={question}
            as="button"
            type="button"
            onClick={() => onSelect(question)}
            px="12px"
            py="10px"
            borderWidth="1px"
            borderStyle="solid"
            borderColor="border.default"
            borderRadius="lg"
            bg="background.page"
            color="text.secondary"
            fontSize="13.5px"
            lineHeight={1.45}
            textAlign="left"
            cursor="pointer"
            _hover={{ borderColor: 'brand.primary', bg: 'brand.tint', color: 'text.primary' }}
          >
            {question}
          </Box>
        ))}
      </Flex>
    </Box>
  );
}
