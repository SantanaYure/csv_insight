import { IconButton, Tooltip, useColorMode } from '@chakra-ui/react';
import { Moon, Sun } from 'lucide-react';

interface ThemeToggleProps {
  size?: number;
}

/** Alterna entre os modos claro e escuro do tema. */
export function ThemeToggle({ size = 44 }: ThemeToggleProps) {
  const { colorMode, toggleColorMode } = useColorMode();
  const isDark = colorMode === 'dark';

  return (
    <Tooltip label="Alternar tema" openDelay={400}>
      <IconButton
        aria-label={isDark ? 'Ativar tema claro' : 'Ativar tema escuro'}
        onClick={toggleColorMode}
        variant="secondary"
        borderColor="border.default"
        width={`${size}px`}
        height={`${size}px`}
        minW={`${size}px`}
        minH={`${size}px`}
        icon={isDark ? <Sun size={19} strokeWidth={1.7} /> : <Moon size={19} strokeWidth={1.7} />}
      />
    </Tooltip>
  );
}
