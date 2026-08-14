import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { Upload } from 'lucide-react';

import type { Dataset } from '../../types/dataset';
import { formatDateTime } from '../../utils/formatDate';
import { SidebarDatasetCard, SidebarGroupLabel, SidebarSuggestions, SidebarTableList } from './SidebarPieces';

interface AppSidebarProps {
  dataset: Dataset;
  suggestions: string[];
  onSelectSuggestion: (question: string) => void;
  onSelectTable: (tableId: string) => void;
  onNewDataset: () => void;
}

/**
 * Sidebar fixa do desktop (272px), oculta abaixo de `lg`. Concentra o
 * contexto do dataset — não há mais links de navegação: o workspace é uma
 * única tela com painéis (Consulta, Dados, Histórico).
 */
export function AppSidebar({
  dataset,
  suggestions,
  onSelectSuggestion,
  onSelectTable,
  onNewDataset,
}: AppSidebarProps) {
  return (
    <Flex
      as="aside"
      aria-label="Contexto do dataset"
      display={{ base: 'none', lg: 'flex' }}
      direction="column"
      gap="26px"
      flex="none"
      width="272px"
      px="20px"
      py="24px"
      borderRightWidth="1px"
      borderRightStyle="solid"
      borderColor="border.default"
      bg="background.surface"
      position="sticky"
      top="64px"
      alignSelf="flex-start"
      maxH="calc(100vh - 64px)"
      overflowY="auto"
    >
      <SidebarDatasetCard dataset={dataset} />

      <Box>
        <SidebarGroupLabel>Tabelas</SidebarGroupLabel>
        <SidebarTableList dataset={dataset} onSelectTable={onSelectTable} />
      </Box>

      {suggestions.length > 0 ? (
        <SidebarSuggestions questions={suggestions} onSelect={onSelectSuggestion} />
      ) : null}

      <Box mt="auto" pt="20px" borderTopWidth="1px" borderTopStyle="solid" borderColor="border.default">
        <Button
          variant="secondary"
          width="100%"
          size="sm"
          minH="44px"
          leftIcon={<Upload size={16} strokeWidth={1.8} />}
          onClick={onNewDataset}
        >
          Carregar novo dataset
        </Button>
        <Text mt="12px" fontSize="12px" lineHeight={1.5} color="text.muted">
          Processado em {formatDateTime(dataset.uploadedAt)}
        </Text>
      </Box>
    </Flex>
  );
}
