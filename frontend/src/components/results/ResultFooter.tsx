import { Flex, IconButton, Text, Tooltip, useToast } from '@chakra-ui/react';
import { Copy, Download, RotateCcw } from 'lucide-react';
import type { ReactNode } from 'react';

interface ResultFooterProps {
  /** Descrição curta do resultado: "Resposta em texto · 1,2 s". */
  label: string;
  /** Conteúdo copiado pelo botão de copiar. */
  copyText?: string;
  /** Conteúdo CSV disponibilizado para download. */
  csv?: { fileName: string; content: string };
  onRetry?: () => void;
  extraActions?: ReactNode;
}

/** Rodapé com metadados e ações das respostas do agente. */
export function ResultFooter({ label, copyText, csv, onRetry, extraActions }: ResultFooterProps) {
  const toast = useToast();

  const handleCopy = async () => {
    if (!copyText) return;
    try {
      await navigator.clipboard.writeText(copyText);
      toast({ title: 'Resposta copiada', status: 'success', duration: 2000, isClosable: true });
    } catch {
      toast({
        title: 'Não foi possível copiar',
        description: 'Copie o conteúdo manualmente.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDownload = () => {
    if (!csv) return;
    // BOM para que o Excel reconheça o UTF-8.
    const blob = new Blob(['﻿', csv.content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = csv.fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Flex
      align="center"
      gap="4px"
      mt="16px"
      pt="14px"
      borderTopWidth="1px"
      borderTopStyle="solid"
      borderColor="border.default"
    >
      <Text flex="1" fontSize="12px" color="text.muted">
        {label}
      </Text>

      {copyText ? (
        <Tooltip label="Copiar resposta" openDelay={400}>
          <IconButton
            aria-label="Copiar resposta"
            variant="icon"
            width="32px"
            height="32px"
            minW="32px"
            onClick={handleCopy}
            icon={<Copy size={15} strokeWidth={1.8} />}
          />
        </Tooltip>
      ) : null}

      {csv ? (
        <Tooltip label="Baixar CSV" openDelay={400}>
          <IconButton
            aria-label="Baixar CSV"
            variant="icon"
            width="32px"
            height="32px"
            minW="32px"
            onClick={handleDownload}
            icon={<Download size={15} strokeWidth={1.8} />}
          />
        </Tooltip>
      ) : null}

      {onRetry ? (
        <Tooltip label="Repetir consulta" openDelay={400}>
          <IconButton
            aria-label="Repetir consulta"
            variant="icon"
            width="32px"
            height="32px"
            minW="32px"
            onClick={onRetry}
            icon={<RotateCcw size={15} strokeWidth={1.8} />}
          />
        </Tooltip>
      ) : null}

      {extraActions}
    </Flex>
  );
}
