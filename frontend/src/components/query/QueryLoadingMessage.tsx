import { Box, Flex, Text } from '@chakra-ui/react';
import { Database } from 'lucide-react';

/** Estado de carregamento da resposta: três pontos animados em amarelo. */
export function QueryLoadingMessage() {
  return (
    <Flex gap="12px" role="status" aria-live="polite">
      <Box
        as="span"
        aria-hidden="true"
        flex="none"
        display="grid"
        placeItems="center"
        width="32px"
        height="32px"
        borderRadius="9px"
        bg="brand.primary"
        color="#111111"
      >
        <Database size={17} strokeWidth={1.9} />
      </Box>

      <Flex
        display="inline-flex"
        align="center"
        gap="12px"
        px="20px"
        py="15px"
        bg="background.surface"
        borderWidth="1px"
        borderStyle="solid"
        borderColor="border.default"
        borderRadius="16px"
        boxShadow="bubble"
      >
        <Flex as="span" gap="5px" aria-hidden="true">
          {[0, 0.18, 0.36].map((delay) => (
            <Box
              key={delay}
              as="span"
              width="7px"
              height="7px"
              borderRadius="full"
              bg="brand.primaryHover"
              animation={`dotPulse 1.1s ease-in-out ${delay}s infinite`}
            />
          ))}
        </Flex>
        <Text m={0} fontSize="14.5px" color="text.muted">
          Analisando os dados…
        </Text>
      </Flex>
    </Flex>
  );
}
