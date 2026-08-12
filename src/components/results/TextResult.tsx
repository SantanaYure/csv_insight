import { Box, Text } from '@chakra-ui/react';

import type { TextQueryResult } from '../../types/query';
import { highlightNumbers } from './highlightNumbers';

/** Resposta em texto: frase principal com os números em destaque. */
export function TextResult({ result }: { result: TextQueryResult }) {
  return (
    <Box>
      <Text m={0} fontSize="15.5px" lineHeight={1.65} color="text.primary">
        {highlightNumbers(result.answer)}
      </Text>
      {result.detail ? (
        <Text mt="10px" fontSize="14px" lineHeight={1.6} color="text.muted">
          {result.detail}
        </Text>
      ) : null}
    </Box>
  );
}
