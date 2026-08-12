import { Box, Flex, useDisclosure } from '@chakra-ui/react';
import { useCallback, useMemo } from 'react';
import { Navigate, Outlet, useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '../components/common/AppHeader';
import { AppSidebar } from '../components/common/AppSidebar';
import { ConfirmationDialog } from '../components/common/ConfirmationDialog';
import { LoadingState } from '../components/common/LoadingState';
import { MobileNavigation } from '../components/common/MobileNavigation';
import { useDataset } from '../hooks/useDataset';
import { datasetStore } from '../services/datasetStore';
import { buildSuggestedQuestions } from '../services/query/queryEngine';
import type { Dataset } from '../types/dataset';

export interface ApplicationOutletContext {
  dataset: Dataset;
  /** Perguntas sugeridas derivadas das colunas do conjunto carregado. */
  suggestions: string[];
}

/**
 * Layout interno: header, sidebar fixa no desktop, drawer no mobile e a área
 * principal de conteúdo — que é sempre a mesma tela (o workspace do
 * dataset). A troca entre Consulta, Dados e Histórico acontece por um
 * parâmetro de URL (`?panel=`), não por rotas separadas.
 */
export function ApplicationLayout() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const drawer = useDisclosure();
  const newDatasetDialog = useDisclosure();

  const { dataset, isLoading, error } = useDataset(datasetId);

  const suggestions = useMemo(() => {
    if (!datasetId || !dataset) return [];
    const semantics = datasetStore.semantics(datasetId);
    return semantics ? buildSuggestedQuestions(semantics) : [];
  }, [dataset, datasetId]);

  const handleSelectTable = useCallback(
    (tableId: string) => {
      if (!datasetId) return;
      drawer.onClose();
      navigate(`/datasets/${datasetId}?panel=data&table=${encodeURIComponent(tableId)}`);
    },
    [datasetId, drawer, navigate],
  );

  const handleSelectSuggestion = useCallback(
    (question: string) => {
      if (!datasetId) return;
      navigate(`/datasets/${datasetId}?panel=chat&q=${encodeURIComponent(question)}`);
    },
    [datasetId, navigate],
  );

  if (isLoading) {
    return (
      <Flex direction="column" minH="100vh" bg="background.page">
        <AppHeader variant="application" />
        <LoadingState label="Carregando dataset…" minH="60vh" />
      </Flex>
    );
  }

  // Sem conjunto carregado não há o que exibir: o fluxo volta para o upload.
  if (error || !dataset) {
    return <Navigate to="/upload" replace state={{ reason: 'missing-dataset' }} />;
  }

  return (
    <Flex direction="column" minH="100vh" bg="background.page">
      <AppHeader
        variant="application"
        datasetName={dataset.name}
        onOpenMenu={drawer.onOpen}
        onPrimaryAction={newDatasetDialog.onOpen}
      />

      <Flex flex="1" minH={0} align="stretch">
        <AppSidebar
          dataset={dataset}
          suggestions={suggestions}
          onSelectSuggestion={handleSelectSuggestion}
          onSelectTable={handleSelectTable}
          onNewDataset={newDatasetDialog.onOpen}
        />

        <Box as="main" flex="1" minW={0} display="flex" flexDirection="column">
          <Outlet context={{ dataset, suggestions } satisfies ApplicationOutletContext} />
        </Box>
      </Flex>

      <MobileNavigation
        isOpen={drawer.isOpen}
        onClose={drawer.onClose}
        dataset={dataset}
        onSelectTable={handleSelectTable}
        onNewDataset={newDatasetDialog.onOpen}
      />

      <ConfirmationDialog
        isOpen={newDatasetDialog.isOpen}
        title="Carregar novo dataset?"
        description="O dataset atual e o histórico da sessão serão descartados. Essa ação não pode ser desfeita."
        confirmLabel="Carregar novo"
        onCancel={newDatasetDialog.onClose}
        onConfirm={() => {
          newDatasetDialog.onClose();
          navigate('/upload');
        }}
      />
    </Flex>
  );
}

export default ApplicationLayout;
