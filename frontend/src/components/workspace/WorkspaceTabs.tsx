import { Box, Flex } from '@chakra-ui/react';
import { Clock, MessageSquare, Table2 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { pageGutter } from '../../theme';

export type WorkspacePanel = 'chat' | 'data' | 'history';

interface PanelOption {
  key: WorkspacePanel;
  label: string;
  icon: LucideIcon;
}

const PANELS: PanelOption[] = [
  { key: 'chat', label: 'Consulta', icon: MessageSquare },
  { key: 'data', label: 'Dados', icon: Table2 },
  { key: 'history', label: 'Histórico', icon: Clock },
];

interface WorkspaceTabsProps {
  active: WorkspacePanel;
  onChange: (panel: WorkspacePanel) => void;
  trailing?: React.ReactNode;
}

/**
 * Controle segmentado que substitui a navegação por páginas separadas.
 * Ocupa a largura toda em telas pequenas (alvos de toque generosos) e fica
 * compacto à esquerda a partir do desktop.
 */
export function WorkspaceTabs({ active, onChange, trailing }: WorkspaceTabsProps) {
  return (
    <Flex
      as="nav"
      aria-label="Seções do dataset"
      position="sticky"
      top="64px"
      zIndex={20}
      align="center"
      gap="12px"
      wrap="wrap"
      px={pageGutter}
      py={{ base: '10px', md: '14px' }}
      bg="background.page"
      borderBottomWidth="1px"
      borderBottomStyle="solid"
      borderColor="border.default"
    >
      <Flex
        flex={{ base: '1 1 100%', md: '0 0 auto' }}
        gap="2px"
        p="3px"
        bg="background.subtle"
        borderRadius="12px"
      >
        {PANELS.map((panel) => {
          const Icon = panel.icon;
          const isActive = panel.key === active;
          return (
            <Box
              key={panel.key}
              as="button"
              type="button"
              onClick={() => onChange(panel.key)}
              aria-current={isActive ? 'true' : undefined}
              display="flex"
              alignItems="center"
              justifyContent="center"
              gap="7px"
              flex={{ base: 1, md: '0 0 auto' }}
              minH={{ base: '44px', md: '40px' }}
              px="16px"
              border={0}
              borderRadius="9px"
              bg={isActive ? 'background.surface' : 'transparent'}
              boxShadow={isActive ? 'card' : 'none'}
              color={isActive ? 'text.primary' : 'text.muted'}
              fontSize="14px"
              fontWeight={600}
              cursor="pointer"
              whiteSpace="nowrap"
              _hover={isActive ? undefined : { color: 'text.secondary' }}
            >
              <Icon size={15} strokeWidth={1.9} />
              {panel.label}
            </Box>
          );
        })}
      </Flex>

      <Box flex="1" display={{ base: 'none', md: 'block' }} />

      {trailing}
    </Flex>
  );
}
