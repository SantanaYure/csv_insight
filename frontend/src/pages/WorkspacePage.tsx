import { Flex } from '@chakra-ui/react';
import { useCallback, useEffect, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';

import { ChatPanel } from '../components/workspace/ChatPanel';
import { DataPanel } from '../components/workspace/DataPanel';
import { HistoryPanel } from '../components/workspace/HistoryPanel';
import { WorkspaceTabs, type WorkspacePanel } from '../components/workspace/WorkspaceTabs';
import type { ApplicationOutletContext } from '../layouts/ApplicationLayout';

const PANEL_KEYS: WorkspacePanel[] = ['chat', 'data', 'history'];

/**
 * Interface B do desafio: um único workspace por dataset, com Consulta,
 * Dados e Histórico como painéis alternados por `?panel=`, em vez de rotas
 * separadas. Isso mantém o fluxo em duas telas (Upload → Workspace) tanto
 * no desktop quanto no celular.
 */
export function WorkspacePage() {
  const { dataset, suggestions } = useOutletContext<ApplicationOutletContext>();
  const [searchParams, setSearchParams] = useSearchParams();

  const rawPanel = searchParams.get('panel');
  const panel: WorkspacePanel = PANEL_KEYS.includes(rawPanel as WorkspacePanel)
    ? (rawPanel as WorkspacePanel)
    : 'chat';

  const selectedTableId = searchParams.get('table');
  const pendingFromUrl = searchParams.get('q');

  const [pendingQuestion, setPendingQuestion] = useState('');

  // Uma pergunta chegando pela URL (sugestão da sidebar) é consumida uma
  // única vez e removida, para não reaparecer em navegações futuras.
  useEffect(() => {
    if (!pendingFromUrl) return;
    setPendingQuestion(pendingFromUrl);
    const next = new URLSearchParams(searchParams);
    next.delete('q');
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingFromUrl]);

  const goToPanel = useCallback(
    (nextPanel: WorkspacePanel) => {
      const next = new URLSearchParams(searchParams);
      next.set('panel', nextPanel);
      if (nextPanel !== 'data') next.delete('table');
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const selectTable = useCallback(
    (tableId: string | null) => {
      const next = new URLSearchParams(searchParams);
      next.set('panel', 'data');
      if (tableId) next.set('table', tableId);
      else next.delete('table');
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const askAgain = useCallback(
    (question: string) => {
      if (question) setPendingQuestion(question);
      goToPanel('chat');
    },
    [goToPanel],
  );

  return (
    <Flex direction="column" flex="1" minH={0}>
      <WorkspaceTabs active={panel} onChange={goToPanel} />

      {panel === 'chat' ? (
        <Flex direction="column" flex="1" minH={0}>
          <ChatPanel
            dataset={dataset}
            suggestions={suggestions}
            pendingQuestion={pendingQuestion}
            onConsumePending={() => setPendingQuestion('')}
          />
        </Flex>
      ) : panel === 'data' ? (
        <DataPanel dataset={dataset} selectedTableId={selectedTableId} onSelectTable={selectTable} />
      ) : (
        <HistoryPanel datasetId={dataset.id} onAskAgain={askAgain} />
      )}
    </Flex>
  );
}

export default WorkspacePage;
