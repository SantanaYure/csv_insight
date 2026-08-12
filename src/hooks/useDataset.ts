import { useCallback, useEffect, useState } from 'react';

import { dataService } from '../services';
import type { Dataset } from '../types/dataset';

interface UseDatasetResult {
  dataset: Dataset | null;
  isLoading: boolean;
  error: string | null;
  reload: () => void;
}

/** Carrega o dataset atual a partir do `dataService`. */
export function useDataset(datasetId: string | undefined): UseDatasetResult {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(datasetId));
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  useEffect(() => {
    if (!datasetId) {
      setDataset(null);
      setIsLoading(false);
      setError('Nenhum dataset informado.');
      return;
    }

    let active = true;
    setIsLoading(true);
    setError(null);

    dataService
      .getDataset(datasetId)
      .then((result) => {
        if (active) setDataset(result);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(cause instanceof Error ? cause.message : 'Não foi possível carregar o dataset.');
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [datasetId, reloadToken]);

  return { dataset, isLoading, error, reload };
}
