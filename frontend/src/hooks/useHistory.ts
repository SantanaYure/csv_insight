import { useCallback, useEffect, useState } from 'react';

import { dataService } from '../services';
import type { ChatMessage } from '../types/message';

interface UseHistoryResult {
  items: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  remove: (messageId: string) => Promise<void>;
  reload: () => void;
}

/** Carrega e mantém o histórico de consultas do dataset. */
export function useHistory(datasetId: string | undefined): UseHistoryResult {
  const [items, setItems] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(datasetId));
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((token) => token + 1), []);

  useEffect(() => {
    if (!datasetId) {
      setItems([]);
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);
    setError(null);

    dataService
      .getHistory(datasetId)
      .then((result) => {
        if (active) setItems(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(
            cause instanceof Error ? cause.message : 'Não foi possível carregar o histórico.',
          );
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [datasetId, reloadToken]);

  const remove = useCallback(
    async (messageId: string) => {
      if (!datasetId) return;
      await dataService.deleteHistoryItem(datasetId, messageId);
      setItems((current) => current.filter((item) => item.id !== messageId));
    },
    [datasetId],
  );

  return { items, isLoading, error, remove, reload };
}
