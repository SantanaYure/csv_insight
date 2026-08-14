import { Box, Flex, IconButton, Spinner, Text } from '@chakra-ui/react';
import { FileText, X } from 'lucide-react';

import { formatFileSize } from '../../utils/formatFileSize';
import { UploadProgress } from './UploadProgress';

interface SelectedFileCardProps {
  file: File;
  /** Progresso do envio; exibido apenas durante o upload. */
  uploadProgress?: number;
  isUploading?: boolean;
  onRemove: () => void;
}

/** Card do arquivo selecionado com nome, tamanho, progresso e remoção. */
export function SelectedFileCard({
  file,
  uploadProgress = 0,
  isUploading = false,
  onRemove,
}: SelectedFileCardProps) {
  return (
    <Flex
      align="center"
      gap="14px"
      mt="18px"
      p="16px"
      borderWidth="1px"
      borderStyle="solid"
      borderColor="border.default"
      borderRadius="xl"
      bg="background.surface"
    >
      <Box
        as="span"
        flex="none"
        display="grid"
        placeItems="center"
        width="42px"
        height="42px"
        borderRadius="lg"
        bg="brand.tint"
        borderWidth="1px"
        borderStyle="solid"
        borderColor="brand.soft"
        color="brand.primaryHover"
      >
        <FileText size={20} strokeWidth={1.8} />
      </Box>

      <Box flex="1" minW={0}>
        <Text m={0} fontSize="15px" fontWeight={600} color="text.primary" noOfLines={1}>
          {file.name}
        </Text>
        <Text mt="3px" fontSize="13.5px" color="text.muted">
          {formatFileSize(file.size)}
        </Text>

        {isUploading ? (
          <UploadProgress
            value={uploadProgress}
            label={`Enviando… ${Math.round(uploadProgress)}%`}
          />
        ) : null}
      </Box>

      {isUploading ? (
        <Spinner label="" flex="none" thickness="2px" speed="0.8s" boxSize="18px" />
      ) : null}

      <IconButton
        aria-label="Remover arquivo"
        title="Remover arquivo"
        variant="secondary"
        borderColor="border.default"
        color="text.muted"
        flex="none"
        width="44px"
        height="44px"
        minW="44px"
        onClick={onRemove}
        icon={<X size={17} strokeWidth={1.8} />}
      />
    </Flex>
  );
}
