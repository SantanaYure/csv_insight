import { Box, Button, Flex, Heading, Progress, Spinner, Text } from '@chakra-ui/react';
import { X } from 'lucide-react';

import { PageContainer } from '../components/common/PageContainer';
import { SurfaceCard } from '../components/common/SurfaceCard';
import { ProcessingSteps } from '../components/upload/ProcessingSteps';
import type { ProcessingStep } from '../types/dataset';
import type { UploadStatus } from '../hooks/useUploadDataset';

interface ProcessingViewProps {
  fileName: string;
  status: UploadStatus;
  processingProgress: number;
  steps: ProcessingStep[];
  completedSteps: number;
  error: string | null;
  onRetry: () => void;
  onChooseAnother: () => void;
}

/**
 * Tela de processamento exibida após o envio: progresso geral e as seis
 * etapas. Em caso de falha mostra a variação de erro do design.
 */
export function ProcessingView({
  fileName,
  status,
  processingProgress,
  steps,
  completedSteps,
  error,
  onRetry,
  onChooseAnother,
}: ProcessingViewProps) {
  if (status === 'error') {
    return (
      <PageContainer
        maxContentWidth="720px"
        pt={{ base: '48px', lg: '64px' }}
        pb={{ base: '56px', lg: '72px' }}
      >
        <Flex align="center" gap="10px">
          <Box
            as="span"
            aria-hidden="true"
            display="grid"
            placeItems="center"
            width="18px"
            height="18px"
            borderRadius="full"
            bg="feedback.error"
            color="#FFFFFF"
          >
            <X size={11} strokeWidth={3} />
          </Box>
          <Text
            m={0}
            fontSize="13px"
            fontWeight={600}
            letterSpacing="0.06em"
            textTransform="uppercase"
            color="feedback.error"
          >
            Processamento interrompido
          </Text>
        </Flex>

        <Heading as="h1" size="h1" mt="16px">
          Não foi possível preparar os dados
        </Heading>
        <Text mt="12px" fontSize="17px" lineHeight={1.6} color="text.muted">
          {error ?? 'Ocorreu uma falha ao ler o conteúdo do arquivo enviado.'}
        </Text>

        <SurfaceCard mt="32px" p="28px">
          <ProcessingSteps steps={steps.map(markFailure)} />
          <Flex gap="10px" wrap="wrap" mt="24px">
            <Button variant="primary" onClick={onRetry}>
              Tentar novamente
            </Button>
            <Button variant="secondary" onClick={onChooseAnother}>
              Escolher outro arquivo
            </Button>
          </Flex>
        </SurfaceCard>
      </PageContainer>
    );
  }

  const isComplete = status === 'success';

  return (
    <PageContainer
      maxContentWidth="720px"
      pt={{ base: '48px', lg: '64px' }}
      pb={{ base: '56px', lg: '72px' }}
    >
      <Flex align="center" gap="10px" role="status" aria-live="polite">
        {!isComplete ? <Spinner label="" thickness="2px" speed="0.8s" boxSize="16px" /> : null}
        <Text
          m={0}
          fontSize="13px"
          fontWeight={600}
          letterSpacing="0.06em"
          textTransform="uppercase"
          color="text.muted"
        >
          {isComplete ? 'Concluído' : 'Processando'}
        </Text>
      </Flex>

      <Heading as="h1" size="h1" mt="16px">
        {isComplete ? 'Seus dados estão prontos' : 'Preparando seus dados'}
      </Heading>
      <Text mt="12px" fontSize="17px" lineHeight={1.6} color="text.muted">
        {isComplete
          ? 'Abrindo o resumo do conjunto de dados…'
          : 'Estamos processando os arquivos e criando o ambiente de consulta.'}
      </Text>

      <SurfaceCard mt="32px" p="28px">
        <Flex align="baseline" justify="space-between" gap="12px">
          <Text m={0} fontSize="15px" fontWeight={600} color="text.primary">
            {fileName}
          </Text>
          <Text m={0} fontSize="26px" fontWeight={700} letterSpacing="-0.02em" color="text.primary">
            {processingProgress}
            <Text as="span" fontSize="16px" fontWeight={600} color="text.muted">
              %
            </Text>
          </Text>
        </Flex>

        <Progress
          mt="12px"
          height="8px"
          borderRadius="full"
          value={processingProgress}
          aria-label="Progresso do processamento"
        />

        <Text mt="10px" fontSize="13.5px" color="text.muted">
          {completedSteps} de {steps.length} etapas concluídas
        </Text>

        <ProcessingSteps steps={steps} />
      </SurfaceCard>

      <Flex align="center" gap="12px" wrap="wrap" mt="22px">
        <Text m={0} fontSize="13.5px" color="text.muted">
          Você pode fechar esta aba: o processamento continua.
        </Text>
      </Flex>
    </PageContainer>
  );
}

function markFailure(step: ProcessingStep): ProcessingStep {
  return step.status === 'running' ? { ...step, status: 'error' } : step;
}
