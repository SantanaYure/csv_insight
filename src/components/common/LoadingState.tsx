import { Flex, Spinner, Text } from '@chakra-ui/react';

interface LoadingStateProps {
  label?: string;
  minH?: string;
}

/** Indicador de carregamento de página com texto acessível. */
export function LoadingState({ label = 'Carregando…', minH = '240px' }: LoadingStateProps) {
  return (
    <Flex
      role="status"
      aria-live="polite"
      direction="column"
      align="center"
      justify="center"
      gap="14px"
      minH={minH}
      width="100%"
    >
      <Spinner label="" thickness="2px" speed="0.8s" size="lg" />
      <Text fontSize="14.5px" color="text.muted">
        {label}
      </Text>
    </Flex>
  );
}
