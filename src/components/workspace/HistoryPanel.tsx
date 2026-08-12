import {
  Box,
  Button,
  Flex,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Text,
  Tooltip,
  useDisclosure,
  useToast,
  VisuallyHidden,
} from '@chakra-ui/react';
import { Clock, Copy, Search, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';

import { ConfirmationDialog } from '../common/ConfirmationDialog';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';
import { StatusBadge } from '../common/StatusBadge';
import { SurfaceCard } from '../common/SurfaceCard';
import { resultToPlainText, summarizeResult } from '../results/resultUtils';
import { pageGutter } from '../../theme';
import { useHistory } from '../../hooks/useHistory';
import type { ChatMessage } from '../../types/message';
import { QUERY_RESULT_LABEL, type QueryResultType } from '../../types/query';
import { formatRelativeDateTime } from '../../utils/formatDate';

interface HistoryPanelProps {
  datasetId: string;
  /** Reabre a pergunta selecionada no painel de Consulta. */
  onAskAgain: (question: string) => void;
}

const FILTERS: { key: 'all' | QueryResultType; label: string }[] = [
  { key: 'all', label: 'Todos' },
  { key: 'text', label: 'Texto' },
  { key: 'table', label: 'Tabela' },
  { key: 'chart', label: 'Gráfico' },
  { key: 'combined', label: 'Combinado' },
];

/** Painel "Histórico": perguntas e respostas anteriores, com busca e filtro. */
export function HistoryPanel({ datasetId, onAskAgain }: HistoryPanelProps) {
  const toast = useToast();
  const deleteDialog = useDisclosure();

  const { items, isLoading, remove } = useHistory(datasetId);
  const [filter, setFilter] = useState<'all' | QueryResultType>('all');
  const [search, setSearch] = useState('');
  const [pendingDeletion, setPendingDeletion] = useState<ChatMessage | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();

    return items.filter((item) => {
      const matchesFilter = filter === 'all' || item.result?.type === filter;
      if (!matchesFilter) return false;
      if (!term) return true;

      const haystack = [item.question ?? item.content, item.result ? summarizeResult(item.result) : '']
        .join(' ')
        .toLowerCase();

      return haystack.includes(term);
    });
  }, [filter, items, search]);

  const handleCopy = async (item: ChatMessage) => {
    const text = [item.question ?? item.content, item.result ? resultToPlainText(item.result) : '']
      .filter(Boolean)
      .join('\n\n');

    try {
      await navigator.clipboard.writeText(text);
      toast({ title: 'Consulta copiada', status: 'success', duration: 2000, isClosable: true });
    } catch {
      toast({ title: 'Não foi possível copiar', status: 'error', duration: 3000, isClosable: true });
    }
  };

  const confirmDelete = async () => {
    if (!pendingDeletion) return;
    setIsDeleting(true);
    try {
      await remove(pendingDeletion.id);
      toast({ title: 'Consulta excluída', status: 'success', duration: 2000, isClosable: true });
    } finally {
      setIsDeleting(false);
      setPendingDeletion(null);
      deleteDialog.onClose();
    }
  };

  return (
    <Box px={pageGutter} pt="24px" pb="56px" maxW="1000px" mx="auto" width="100%">
      <Flex align="center" gap="12px" wrap="wrap">
        <InputGroup flex="1" minW="220px">
          <InputLeftElement height="44px" width="40px" pointerEvents="none" color="text.muted">
            <Search size={17} strokeWidth={1.9} />
          </InputLeftElement>
          <VisuallyHidden>
            <label htmlFor="history-search">Buscar no histórico</label>
          </VisuallyHidden>
          <Input
            id="history-search"
            type="search"
            pl="40px"
            placeholder="Buscar por pergunta ou resposta"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </InputGroup>

        <Flex role="group" aria-label="Filtrar por tipo de resposta" gap="7px" wrap="wrap">
          {FILTERS.map((option) => {
            const isActive = filter === option.key;
            return (
              <Button
                key={option.key}
                onClick={() => setFilter(option.key)}
                aria-pressed={isActive}
                minH="38px"
                px="14px"
                borderRadius="full"
                fontSize="13.5px"
                fontWeight={600}
                bg={isActive ? 'brand.primary' : 'background.surface'}
                borderWidth="1px"
                borderStyle="solid"
                borderColor={isActive ? 'brand.primaryHover' : 'border.default'}
                color={isActive ? 'brand.textOnPrimary' : 'text.secondary'}
                _hover={{ bg: isActive ? 'brand.primaryHover' : 'background.subtle' }}
              >
                {option.label}
              </Button>
            );
          })}
        </Flex>
      </Flex>

      {isLoading ? (
        <LoadingState label="Carregando histórico…" />
      ) : filtered.length > 0 ? (
        <Flex direction="column" gap="12px" mt="22px">
          {filtered.map((item) => (
            <HistoryItem
              key={item.id}
              item={item}
              onView={() => onAskAgain(item.question ?? item.content)}
              onCopy={() => void handleCopy(item)}
              onDelete={() => {
                setPendingDeletion(item);
                deleteDialog.onOpen();
              }}
            />
          ))}
        </Flex>
      ) : (
        <SurfaceCard mt="22px" px="24px" py="64px" elevated={false}>
          <EmptyState
            tone="neutral"
            icon={
              <Box color="text.muted">
                <Clock size={26} strokeWidth={1.7} />
              </Box>
            }
            title="Nenhuma consulta encontrada"
            description={
              items.length === 0
                ? 'As perguntas realizadas aparecerão aqui.'
                : 'Ajuste a busca ou o filtro para encontrar uma consulta.'
            }
            action={
              <Button variant="primary" onClick={() => onAskAgain('')}>
                Fazer uma pergunta
              </Button>
            }
          />
        </SurfaceCard>
      )}

      <ConfirmationDialog
        isOpen={deleteDialog.isOpen}
        title="Excluir esta consulta?"
        description="A pergunta e a resposta serão removidas do histórico. Essa ação não pode ser desfeita."
        confirmLabel="Excluir"
        tone="danger"
        isLoading={isDeleting}
        onCancel={() => {
          setPendingDeletion(null);
          deleteDialog.onClose();
        }}
        onConfirm={() => void confirmDelete()}
      />
    </Box>
  );
}

function HistoryItem({
  item,
  onView,
  onCopy,
  onDelete,
}: {
  item: ChatMessage;
  onView: () => void;
  onCopy: () => void;
  onDelete: () => void;
}) {
  const type = item.result?.type ?? 'text';

  return (
    <SurfaceCard px={{ base: '16px', md: '22px' }} py="20px">
      <Flex align="center" gap="10px" wrap="wrap">
        <StatusBadge tone={type === 'error' ? 'error' : 'soft'} height="24px" px="10px" fontSize="12px">
          {QUERY_RESULT_LABEL[type]}
        </StatusBadge>
        <Text m={0} fontSize="12.5px" color="text.muted">
          {formatRelativeDateTime(item.createdAt)}
        </Text>
      </Flex>

      <Text mt="12px" fontSize="16px" fontWeight={600} lineHeight={1.5} color="text.primary">
        {item.question ?? item.content}
      </Text>
      <Text mt="7px" fontSize="14.5px" lineHeight={1.6} color="text.muted">
        {item.result ? summarizeResult(item.result) : '—'}
      </Text>

      <Flex
        align="center"
        gap="8px"
        wrap="wrap"
        mt="16px"
        pt="15px"
        borderTopWidth="1px"
        borderTopStyle="solid"
        borderColor="border.default"
      >
        <Button variant="secondary" size="sm" minH="40px" onClick={onView}>
          Ver novamente
        </Button>
        <Button
          variant="subtle"
          size="sm"
          minH="40px"
          leftIcon={<Copy size={15} strokeWidth={1.8} />}
          onClick={onCopy}
        >
          Copiar
        </Button>

        <Box flex="1" />

        <Tooltip label="Excluir consulta" openDelay={400}>
          <IconButton
            aria-label="Excluir consulta"
            variant="subtle"
            width="40px"
            height="40px"
            minW="40px"
            minH="40px"
            color="text.muted"
            _hover={{ borderColor: 'feedback.error', color: 'feedback.error' }}
            onClick={onDelete}
            icon={<Trash2 size={16} strokeWidth={1.8} />}
          />
        </Tooltip>
      </Flex>
    </SurfaceCard>
  );
}
