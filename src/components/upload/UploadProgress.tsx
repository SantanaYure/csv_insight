import { Box, Progress, Text } from '@chakra-ui/react';

interface UploadProgressProps {
  value: number;
  label?: string;
  /** Barra fina (6px) usada dentro do card do arquivo. */
  size?: 'sm' | 'md';
}

/** Barra de progresso do envio, com rótulo percentual. */
export function UploadProgress({ value, label, size = 'sm' }: UploadProgressProps) {
  const rounded = Math.round(value);

  return (
    <Box mt="10px">
      <Progress
        value={rounded}
        height={size === 'sm' ? '6px' : '8px'}
        borderRadius="full"
        aria-label="Progresso do envio"
      />
      {label ? (
        <Text mt="7px" fontSize="12.5px" color="text.muted">
          {label}
        </Text>
      ) : null}
    </Box>
  );
}
