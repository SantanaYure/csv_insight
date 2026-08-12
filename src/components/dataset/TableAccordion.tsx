import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Flex,
  Heading,
  Text,
} from '@chakra-ui/react';
import { Download, Table2 } from 'lucide-react';
import { useEffect, useRef } from 'react';

import type { DatasetTable } from '../../types/dataset';
import { formatNumber } from '../../utils/formatNumber';
import { ColumnList } from './ColumnList';
import { DataPreview } from './DataPreview';

interface TableAccordionProps {
  tables: DatasetTable[];
  /** Id da tabela expandida, controlada pela URL (`?table=`). */
  expandedTable: string | null;
  onToggle: (tableId: string | null) => void;
}

/**
 * Lista as tabelas do dataset como um acordeão: cada item expande no lugar
 * para mostrar colunas e amostra de registros, sem trocar de tela.
 */
export function TableAccordion({ tables, expandedTable, onToggle }: TableAccordionProps) {
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const expandedIndex = expandedTable ? tables.findIndex((table) => table.id === expandedTable) : -1;

  useEffect(() => {
    if (!expandedTable) return;
    buttonRefs.current[expandedTable]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [expandedTable]);

  return (
    <Accordion
      index={expandedIndex}
      onChange={(nextIndex) => {
        const index = nextIndex as number;
        onToggle(index >= 0 ? tables[index].id : null);
      }}
      allowToggle
      display="flex"
      flexDirection="column"
      gap="12px"
    >
      {tables.map((table) => (
        <AccordionItem
          key={table.id}
          borderWidth="1px"
          borderStyle="solid"
          borderColor="border.default"
          borderRadius="2xl"
          overflow="hidden"
          bg="background.surface"
        >
          <AccordionButton
            ref={(node) => {
              buttonRefs.current[table.id] = node;
            }}
            px={{ base: '16px', md: '20px' }}
            py="16px"
            gap="14px"
            _hover={{ bg: 'background.subtle' }}
          >
            <Box
              as="span"
              aria-hidden="true"
              flex="none"
              display="grid"
              placeItems="center"
              width="34px"
              height="34px"
              borderRadius="lg"
              bg="brand.tint"
              borderWidth="1px"
              borderStyle="solid"
              borderColor="brand.soft"
              color="brand.primaryHover"
            >
              <Table2 size={16} strokeWidth={1.8} />
            </Box>

            <Box flex="1" minW={0} textAlign="left">
              <Text m={0} fontSize="15.5px" fontWeight={600} fontFamily="mono" color="text.primary">
                {table.name}
              </Text>
              <Text mt="2px" fontSize="13px" color="text.muted" noOfLines={1}>
                {table.description}
              </Text>
            </Box>

            <Flex gap="18px" flex="none" display={{ base: 'none', sm: 'flex' }}>
              <Metric value={formatNumber(table.rowCount)} label="registros" />
              <Metric value={String(table.columnCount)} label="colunas" />
            </Flex>

            <AccordionIcon flex="none" color="text.muted" />
          </AccordionButton>

          <AccordionPanel
            px={{ base: '16px', md: '20px' }}
            pb="20px"
            pt="4px"
            borderTopWidth="1px"
            borderTopStyle="solid"
            borderColor="border.default"
          >
            <Flex
              display={{ base: 'flex', sm: 'none' }}
              gap="18px"
              mt="14px"
              mb="6px"
            >
              <Metric value={formatNumber(table.rowCount)} label="registros" />
              <Metric value={String(table.columnCount)} label="colunas" />
            </Flex>

            <Heading as="h3" mt="14px" mb="10px" fontSize="14px" fontWeight={600} color="text.primary">
              Colunas
            </Heading>
            <ColumnList columns={table.columns} caption={`Colunas da tabela ${table.name}`} />

            <Heading as="h3" mt="20px" mb="10px" fontSize="14px" fontWeight={600} color="text.primary">
              Amostra dos registros
            </Heading>
            <DataPreview
              columns={table.columns}
              rows={table.preview}
              caption={`Amostra de registros da tabela ${table.name}`}
            />

            <Flex align="center" justify="space-between" gap="12px" wrap="wrap" mt="14px">
              <Text m={0} fontSize="12.5px" color="text.muted">
                Mostrando {table.preview.length} de {formatNumber(table.rowCount)} registros
              </Text>
              <Button
                variant="subtle"
                size="sm"
                minH="40px"
                leftIcon={<Download size={15} strokeWidth={1.8} />}
                onClick={() => downloadSample(table)}
              >
                Baixar amostra
              </Button>
            </Flex>
          </AccordionPanel>
        </AccordionItem>
      ))}
    </Accordion>
  );
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <Box>
      <Text m={0} fontSize="14.5px" fontWeight={600} color="text.primary" textAlign="right">
        {value}
      </Text>
      <Text mt="1px" fontSize="11.5px" color="text.muted" textAlign="right">
        {label}
      </Text>
    </Box>
  );
}

function downloadSample(table: DatasetTable): void {
  const header = table.columns.map((column) => column.name).join(';');
  const rows = table.preview.map((row) =>
    table.columns.map((column) => String(row[column.name] ?? '')).join(';'),
  );
  const blob = new Blob(['﻿', [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `amostra_${table.name}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
