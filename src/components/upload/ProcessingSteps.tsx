import { Box, Flex, Text } from '@chakra-ui/react';
import { Check, X } from 'lucide-react';

import type { ProcessingStep } from '../../types/dataset';

interface ProcessingStepsProps {
  steps: ProcessingStep[];
}

const STATUS_LABEL: Record<ProcessingStep['status'], string> = {
  done: 'concluído',
  running: 'em andamento',
  pending: 'aguardando',
  error: 'falhou',
};

/** Lista das seis etapas do processamento, com destaque na etapa corrente. */
export function ProcessingSteps({ steps }: ProcessingStepsProps) {
  return (
    <Flex as="ol" direction="column" gap="2px" listStyleType="none" p={0} m={0} mt="26px">
      {steps.map((step) => (
        <Flex
          as="li"
          key={step.id}
          align="center"
          gap="14px"
          px="14px"
          py="13px"
          borderRadius="lg"
          bg={step.status === 'running' ? 'brand.tint' : 'transparent'}
          borderWidth="1px"
          borderStyle="solid"
          borderColor={
            step.status === 'running'
              ? 'brand.soft'
              : step.status === 'error'
                ? 'border.strong'
                : 'transparent'
          }
          borderLeftWidth={step.status === 'error' ? '3px' : '1px'}
          borderLeftColor={step.status === 'error' ? 'feedback.error' : undefined}
        >
          <StepIndicator status={step.status} />

          <Text
            flex="1"
            m={0}
            fontSize="15px"
            fontWeight={step.status === 'pending' ? 400 : step.status === 'running' ? 600 : 500}
            color={step.status === 'pending' ? 'text.muted' : 'text.primary'}
          >
            {step.label}
          </Text>

          <Text
            m={0}
            fontSize="13px"
            fontWeight={step.status === 'running' ? 500 : 400}
            color={
              step.status === 'error'
                ? 'feedback.error'
                : step.status === 'running'
                  ? 'text.secondary'
                  : 'text.muted'
            }
          >
            {(step.status === 'done' || step.status === 'running') && step.detail
              ? step.detail
              : STATUS_LABEL[step.status]}
          </Text>
        </Flex>
      ))}
    </Flex>
  );
}

function StepIndicator({ status }: { status: ProcessingStep['status'] }) {
  if (status === 'done') {
    return (
      <Box
        as="span"
        aria-hidden="true"
        flex="none"
        display="grid"
        placeItems="center"
        width="26px"
        height="26px"
        borderRadius="full"
        bg="brand.primary"
        color="#111111"
      >
        <Check size={15} strokeWidth={2.4} />
      </Box>
    );
  }

  if (status === 'error') {
    return (
      <Box
        as="span"
        aria-hidden="true"
        flex="none"
        display="grid"
        placeItems="center"
        width="26px"
        height="26px"
        borderRadius="full"
        bg="feedback.error"
        color="#FFFFFF"
      >
        <X size={14} strokeWidth={3} />
      </Box>
    );
  }

  if (status === 'running') {
    return (
      <Box
        as="span"
        aria-hidden="true"
        flex="none"
        width="26px"
        height="26px"
        borderRadius="full"
        borderWidth="2.5px"
        borderStyle="solid"
        borderColor="brand.soft"
        borderTopColor="brand.primaryHover"
        animation="spin .8s linear infinite"
        sx={{ '@keyframes spin': { to: { transform: 'rotate(360deg)' } } }}
      />
    );
  }

  return (
    <Box
      as="span"
      aria-hidden="true"
      flex="none"
      width="26px"
      height="26px"
      borderRadius="full"
      borderWidth="1.5px"
      borderStyle="dashed"
      borderColor="border.strong"
    />
  );
}
