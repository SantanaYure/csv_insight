import { useCallback, useEffect, useRef, useState } from 'react';

import { dataService } from '../services';
import type { Dataset, ProcessingStep } from '../types/dataset';
import { formatNumber } from '../utils/formatNumber';

export type UploadStatus =
  | 'idle'
  | 'selected'
  | 'uploading'
  | 'processing'
  | 'success'
  | 'error';

const STEP_IDS = ['received', 'unzipped', 'csv', 'columns', 'prepared', 'environment'] as const;
type StepId = (typeof STEP_IDS)[number];

const STEP_LABELS: Record<StepId, string> = {
  received: 'Arquivo recebido',
  unzipped: 'ZIP descompactado',
  csv: 'Arquivos CSV encontrados',
  columns: 'Colunas identificadas',
  prepared: 'Dados preparados',
  environment: 'Ambiente de consulta criado',
};

const UPLOAD_TICK_MS = 80;
/** Tempo mínimo por etapa, para que o progresso seja legível. */
const MIN_STEP_MS = 420;

function initialSteps(): ProcessingStep[] {
  return STEP_IDS.map((id, index) => ({
    id,
    label: STEP_LABELS[id],
    status: index === 0 ? 'running' : 'pending',
  }));
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

/**
 * Conduz o envio e o processamento do ZIP. As etapas refletem a leitura real
 * do arquivo: a contagem de CSVs e de colunas vem do conjunto carregado.
 */
export function useUploadDataset(): UseUploadDatasetResult {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [steps, setSteps] = useState<ProcessingStep[]>(initialSteps);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  const timers = useRef<number[]>([]);
  const intervals = useRef<number[]>([]);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      timers.current.forEach((id) => window.clearTimeout(id));
      intervals.current.forEach((id) => window.clearInterval(id));
    };
  }, []);

  const clearTimers = useCallback(() => {
    timers.current.forEach((id) => window.clearTimeout(id));
    intervals.current.forEach((id) => window.clearInterval(id));
    timers.current = [];
    intervals.current = [];
  }, []);

  const wait = useCallback(
    (ms: number) =>
      new Promise<void>((resolve) => {
        const id = window.setTimeout(resolve, ms);
        timers.current.push(id);
      }),
    [],
  );

  const advance = useCallback((index: number, detail?: string) => {
    setSteps((current) =>
      current.map((step, stepIndex) => {
        if (stepIndex < index) return step.status === 'done' ? step : { ...step, status: 'done' };
        if (stepIndex === index) return { ...step, status: 'running' };
        return { ...step, status: 'pending' };
      }),
    );
    if (detail !== undefined) {
      setSteps((current) =>
        current.map((step, stepIndex) =>
          stepIndex === index ? { ...step, detail } : step,
        ),
      );
    }
  }, []);

  const selectFile = useCallback(
    (nextFile: File) => {
      clearTimers();
      setFile(nextFile);
      setStatus('selected');
      setUploadProgress(0);
      setSteps(initialSteps());
      setDataset(null);
      setError(null);
    },
    [clearTimers],
  );

  const removeFile = useCallback(() => {
    clearTimers();
    setFile(null);
    setStatus('idle');
    setUploadProgress(0);
    setSteps(initialSteps());
    setDataset(null);
    setError(null);
  }, [clearTimers]);

  const reset = removeFile;

  const runProcessing = useCallback(
    async (uploadedFile: File) => {
      setStatus('processing');

      try {
        advance(0, uploadedFile.name);
        await wait(MIN_STEP_MS);
        if (!mounted.current) return;

        advance(1);
        await wait(MIN_STEP_MS);
        if (!mounted.current) return;

        advance(2, 'lendo o arquivo…');
        // A leitura real do ZIP acontece aqui. Arquivos grandes podem levar
        // algum tempo: o texto da etapa é atualizado conforme cada tabela é
        // processada, para deixar claro que o processamento está avançando.
        const result = await dataService.uploadDataset(uploadedFile, (progress) => {
          if (!mounted.current) return;
          advance(
            2,
            `${progress.fileName} · ${formatNumber(progress.rowCount)} linhas (${progress.tableIndex}/${progress.tableCount})`,
          );
        });
        if (!mounted.current) return;

        const csvCount = result.tables.length + (result.dictionaryFileName ? 1 : 0);
        advance(2, `${csvCount} ${csvCount === 1 ? 'arquivo' : 'arquivos'}`);
        await wait(MIN_STEP_MS);
        if (!mounted.current) return;

        advance(3, `${result.totalColumns} colunas`);
        await wait(MIN_STEP_MS);
        if (!mounted.current) return;

        advance(4, `${formatNumber(result.totalRows)} registros`);
        await wait(MIN_STEP_MS);
        if (!mounted.current) return;

        advance(5, `${result.tables.length} ${result.tables.length === 1 ? 'tabela' : 'tabelas'}`);
        await wait(MIN_STEP_MS);
        if (!mounted.current) return;

        setSteps((current) => current.map((step) => ({ ...step, status: 'done' })));
        setDataset(result);
        setStatus('success');
      } catch (cause: unknown) {
        if (!mounted.current) return;
        setError(
          cause instanceof Error
            ? cause.message
            : 'Não foi possível preparar os dados enviados.',
        );
        setStatus('error');
      }
    },
    [advance, wait],
  );

  const start = useCallback(() => {
    if (!file) return;

    clearTimers();
    setError(null);
    setUploadProgress(0);
    setSteps(initialSteps());
    setStatus('uploading');

    const interval = window.setInterval(() => {
      setUploadProgress((current) => {
        const next = Math.min(100, current + Math.round(6 + Math.random() * 12));
        if (next >= 100) {
          window.clearInterval(interval);
          const handoff = window.setTimeout(() => void runProcessing(file), 200);
          timers.current.push(handoff);
        }
        return next;
      });
    }, UPLOAD_TICK_MS);

    intervals.current.push(interval);
  }, [clearTimers, file, runProcessing]);

  const completedSteps = steps.filter((step) => step.status === 'done').length;
  const processingProgress = Math.round((completedSteps / STEP_IDS.length) * 100);

  return {
    status,
    file,
    uploadProgress,
    processingProgress,
    steps,
    completedSteps,
    dataset,
    error,
    selectFile,
    removeFile,
    start,
    reset,
  };
}
