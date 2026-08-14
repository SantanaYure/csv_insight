import { Box, Button, Flex, IconButton, Text } from '@chakra-ui/react';
import { Database, Menu, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { pageGutter } from '../../theme';
import { Logo } from './Logo';
import { ThemeToggle } from './ThemeToggle';

interface AppHeaderProps {
  /** `public` é o header alto das telas públicas; `application` o interno. */
  variant?: 'public' | 'application';
  /** Nome do dataset exibido ao lado da marca no header interno. */
  datasetName?: string;
  /** Abre o drawer de navegação no mobile. */
  onOpenMenu?: () => void;
  /** Ação do botão primário à direita. */
  onPrimaryAction?: () => void;
}

/**
 * Header sticky com blur. Na variante pública tem 68px de altura e CTA
 * "Carregar dados"; na interna tem 64px, o nome do dataset e "Novo dataset".
 */
export function AppHeader({
  variant = 'public',
  datasetName,
  onOpenMenu,
  onPrimaryAction,
}: AppHeaderProps) {
  const navigate = useNavigate();
  const isPublic = variant === 'public';

  const handlePrimary = () => {
    if (onPrimaryAction) {
      onPrimaryAction();
      return;
    }
    navigate('/upload');
  };

  return (
    <Flex
      as="header"
      position="sticky"
      top={0}
      zIndex={40}
      align="center"
      gap={isPublic ? '16px' : '14px'}
      height={isPublic ? '68px' : '64px'}
      px={pageGutter}
      flex="none"
      bg="background.header"
      backdropFilter="blur(10px)"
      borderBottomWidth="1px"
      borderBottomStyle="solid"
      borderColor="border.default"
    >
      {!isPublic ? (
        <IconButton
          aria-label="Abrir menu"
          title="Abrir menu"
          onClick={onOpenMenu}
          display={{ base: 'grid', lg: 'none' }}
          variant="secondary"
          borderColor="border.default"
          width="40px"
          height="40px"
          minW="40px"
          minH="40px"
          ml="-8px"
          icon={<Menu size={18} strokeWidth={1.9} />}
        />
      ) : null}

      <Box
        as="button"
        type="button"
        onClick={() => navigate('/')}
        aria-label="CSV Insight — início"
        bg="none"
        border={0}
        p={0}
        cursor="pointer"
      >
        <Logo size={isPublic ? 34 : 30} fontSize={isPublic ? '17px' : '16px'} />
      </Box>

      {!isPublic && datasetName ? (
        <>
          <Box
            display={{ base: 'none', lg: 'block' }}
            width="1px"
            height="22px"
            bg="border.default"
          />
          <Flex
            display={{ base: 'none', lg: 'flex' }}
            align="center"
            gap="8px"
            fontSize="14.5px"
            fontWeight={500}
            color="text.secondary"
            minW={0}
          >
            <Database size={15} strokeWidth={1.8} color="currentColor" opacity={0.7} />
            <Text as="span" noOfLines={1}>
              {datasetName}
            </Text>
          </Flex>
        </>
      ) : null}

      <Box flex="1" />

      <ThemeToggle size={isPublic ? 44 : 40} />

      {isPublic ? (
        <Button variant="ghost" display={{ base: 'none', lg: 'inline-flex' }}>
          Ajuda
        </Button>
      ) : null}

      <Button
        variant={isPublic ? 'primary' : 'secondary'}
        onClick={handlePrimary}
        size={isPublic ? 'md' : 'sm'}
        display={isPublic ? 'inline-flex' : { base: 'none', lg: 'inline-flex' }}
        leftIcon={isPublic ? undefined : <Upload size={16} strokeWidth={1.8} />}
        whiteSpace="nowrap"
      >
        {isPublic ? 'Carregar dados' : 'Novo dataset'}
      </Button>
    </Flex>
  );
}
