import { useCallback, useEffect, useRef, useState } from 'react';

import { dataService } from '../services';
import type { UploadProgress } from '../services/DataService';
import type { Dataset, ProcessingStep } from '../types/dataset';
import { formatNumber } from '../utils/formatNumber';

export type UploadStatus =
  | 'idle'
  | 'selected'
  | 'uploading'
  | 'processing'
  | 'success'
  | 'error';

const STEP_IDS = ['received', 'opened', 'csv', 'columns', 'prepared', 'environment'] as const;
type StepId = (typeof STEP_IDS)[number];

const STEP_LABELS: Record<StepId, string> = {
  received: 'Arquivo recebido',
  opened: 'Arquivo aberto',
  csv: 'Dados CSV encontrados',
  columns: 'Colunas identificadas',
  prepared: 'Dados preparados',
  environment: 'Ambiente de consulta criado',
};

function initialSteps(): ProcessingStep[] {
  return STEP_IDS.map((id, index) => ({
    id,
    label: STEP_LABELS[id],
    status: index === 0 ? 'running' : 'pending',
  }));
}

function markTransferComplete(fileName: string) {
  return (current: ProcessingStep[]): ProcessingStep[] =>
    current.map((step, index) =>
      index === 0
        ? { ...step, status: 'done', detail: fileName }
        : index === 1
          ? { ...step, status: 'running', detail: 'Processando no servidor…' }
          : step,
    );
}

function markTableProcessing(progress: UploadProgress) {
  return (current: ProcessingStep[]): ProcessingStep[] =>
    current.map((step, index) => {
      if (index < 2) return { ...step, status: 'done' };
      if (index !== 2) return step;
      return {
        ...step,
        status: 'running',
        detail: `${progress.fileName} · ${formatNumber(progress.rowCount)} linhas (${progress.tableIndex}/${progress.tableCount})`,
      };
    });
}

function buildCompletedSteps(fileName: string, dataset: Dataset): ProcessingStep[] {
  const csvCount = dataset.tables.length + (dataset.dictionaryFileName ? 1 : 0);
  return [
    { id: 'received', label: STEP_LABELS.received, status: 'done', detail: fileName },
    { id: 'opened', label: STEP_LABELS.opened, status: 'done' },
    {
      id: 'csv',
      label: STEP_LABELS.csv,
      status: 'done',
      detail: `${csvCount} ${csvCount === 1 ? 'arquivo' : 'arquivos'}`,
    },
    {
      id: 'columns',
      label: STEP_LABELS.columns,
      status: 'done',
      detail: `${formatNumber(dataset.totalColumns)} colunas`,
    },
    {
      id: 'prepared',
      label: STEP_LABELS.prepared,
      status: 'done',
      detail: `${formatNumber(dataset.totalRows)} registros`,
    },
    {
      id: 'environment',
      label: STEP_LABELS.environment,
      status: 'done',
      detail: `${dataset.tables.length} ${dataset.tables.length === 1 ? 'tabela' : 'tabelas'}`,
    },
  ];
}

interface UseUploadDatasetResult {
  status: UploadStatus;
  file: File | null;
  uploadProgress: number;
  processingProgress: number;
  steps: ProcessingStep[];
  completedSteps: number;
  dataset: Dataset | null;
  error: string | null;
  selectFile: (file: File) => void;
  removeFile: () => void;
  start: () => void;
  reset: () => void;
}

/** Coordena apenas o estado da interface; transporte e ingestão ficam nos serviços. */
export function useUploadDataset(): UseUploadDatasetResult {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [steps, setSteps] = useState<ProcessingStep[]>(initialSteps);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const activeUpload = useRef<AbortController | null>(null);

  const cancelUpload = useCallback(() => {
    activeUpload.current?.abort();
    activeUpload.current = null;
  }, []);

  useEffect(() => cancelUpload, [cancelUpload]);

  const selectFile = useCallback(
    (nextFile: File) => {
      cancelUpload();
      setFile(nextFile);
      setStatus('selected');
      setUploadProgress(0);
      setSteps(initialSteps());
      setDataset(null);
      setError(null);
    },
    [cancelUpload],
  );

  const removeFile = useCallback(() => {
    cancelUpload();
    setFile(null);
    setStatus('idle');
    setUploadProgress(0);
    setSteps(initialSteps());
    setDataset(null);
    setError(null);
  }, [cancelUpload]);

  const start = useCallback(() => {
    if (!file) return;

    cancelUpload();
    const controller = new AbortController();
    activeUpload.current = controller;
    setStatus('uploading');
    setUploadProgress(0);
    setSteps(initialSteps());
    setDataset(null);
    setError(null);

    void dataService
      .uploadDataset(file, {
        signal: controller.signal,
        onUploadProgress: (percentage) => {
          setUploadProgress(percentage);
          if (percentage >= 100) {
            setStatus('processing');
            setSteps(markTransferComplete(file.name));
          }
        },
        onProcessingProgress: (progress) => {
          setStatus('processing');
          setSteps(markTableProcessing(progress));
        },
      })
      .then((result) => {
        if (controller.signal.aborted) return;
        setUploadProgress(100);
        setSteps(buildCompletedSteps(file.name, result));
        setDataset(result);
        setStatus('success');
        activeUpload.current = null;
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          cause instanceof Error
            ? cause.message
            : 'Não foi possível preparar os dados enviados.',
        );
        setStatus('error');
        activeUpload.current = null;
      });
  }, [cancelUpload, file]);

  const completedSteps = steps.filter((step) => step.status === 'done').length;

  return {
    status,
    file,
    uploadProgress,
    processingProgress: Math.round((completedSteps / STEP_IDS.length) * 100),
    steps,
    completedSteps,
    dataset,
    error,
    selectFile,
    removeFile,
    start,
    reset: removeFile,
  };
}
