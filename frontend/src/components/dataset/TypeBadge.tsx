import { Box } from '@chakra-ui/react';
import type { ReactNode } from 'react';

/** Badge quadrado usado para o tipo de dado das colunas. */
export function TypeBadge({ children }: { children: ReactNode }) {
  return (
    <Box
      as="span"
      display="inline-flex"
      alignItems="center"
      height="22px"
      px="8px"
      borderRadius="sm"
      bg="background.subtle"
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
      fontSize="12px"
      fontWeight={500}
      color="text.secondary"
      whiteSpace="nowrap"
    >
      {children}
    </Box>
  );
}
