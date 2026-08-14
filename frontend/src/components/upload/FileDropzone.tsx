import { Box, Button, Flex, Text, VisuallyHidden } from '@chakra-ui/react';
import { Upload } from 'lucide-react';
import { useRef, useState, type DragEvent } from 'react';

interface FileDropzoneProps {
  onSelectFile: (file: File) => void;
  isDisabled?: boolean;
  /** Extensões aceitas e tamanho máximo exibidos na legenda. */
  accept?: string;
  maxSizeLabel?: string;
}

/** Área de arrastar e soltar com fallback para seleção manual do arquivo. */
export function FileDropzone({
  onSelectFile,
  isDisabled = false,
  accept = '.csv,.zip',
  maxSizeLabel = '200 MB',
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const openPicker = () => {
    if (isDisabled) return;
    inputRef.current?.click();
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    if (isDisabled) return;

    const file = event.dataTransfer.files?.[0];
    if (file) onSelectFile(file);
  };

  return (
    <Box
      role="button"
      tabIndex={isDisabled ? -1 : 0}
      aria-label="Selecionar arquivo CSV ou ZIP para envio"
      aria-disabled={isDisabled}
      onClick={openPicker}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openPicker();
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        if (!isDisabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      display="grid"
      placeItems="center"
      gap="6px"
      px="24px"
      py="46px"
      textAlign="center"
      borderWidth="2px"
      borderStyle="dashed"
      borderColor={isDragging ? 'brand.primary' : 'border.strong'}
      borderRadius="2xl"
      bg={isDragging ? 'brand.tint' : 'background.page'}
      cursor={isDisabled ? 'not-allowed' : 'pointer'}
      opacity={isDisabled ? 0.6 : 1}
      transition="border-color .15s ease, background .15s ease"
      _hover={isDisabled ? undefined : { borderColor: 'brand.primary', bg: 'brand.tint' }}
    >
      <VisuallyHidden>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          disabled={isDisabled}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) onSelectFile(file);
            event.target.value = '';
          }}
        />
      </VisuallyHidden>

      <Flex
        display="grid"
        placeItems="center"
        width="56px"
        height="56px"
        borderRadius="2xl"
        bg="brand.primary"
        color="#111111"
        mb="8px"
      >
        <Upload size={26} strokeWidth={1.8} />
      </Flex>

      <Text m={0} fontSize="17px" fontWeight={600} color="text.primary">
        Arraste o CSV ou ZIP até aqui
      </Text>
      <Text m={0} fontSize="14.5px" color="text.muted">
        ou selecione o arquivo no seu computador
      </Text>

      <Button
        mt="16px"
        variant="secondary"
        isDisabled={isDisabled}
        onClick={(event) => {
          event.stopPropagation();
          openPicker();
        }}
      >
        Selecionar arquivo
      </Button>

      <Text mt="14px" fontSize="13px" color="text.muted">
        Formato aceito: CSV ou ZIP · Tamanho máximo: {maxSizeLabel}
      </Text>
    </Box>
  );
}
