/**
 * Paleta base do CSV Insight.
 *
 * A distribuição visual segue 60% branco/cinza-claro, 30% preto/cinza-escuro
 * e 10% amarelo. O amarelo fica reservado para ações primárias, estados
 * ativos, badges, foco, gráficos e indicadores.
 */
export const yellow = {
  50: '#FFFBEA',
  100: '#FFF3BF',
  200: '#FFE680',
  300: '#FFD84D',
  400: '#FFCA28',
  500: '#F5B800',
  600: '#D99D00',
  700: '#A97400',
  800: '#704D00',
  900: '#3D2A00',
} as const;

export const gray = {
  50: '#FAFAFA',
  100: '#F5F5F5',
  200: '#E5E5E5',
  300: '#D1D1D1',
  400: '#A3A3A3',
  500: '#7A7A7A',
  600: '#5F5F5F',
  700: '#404040',
  800: '#2D2D2D',
  900: '#1F1F1F',
  950: '#171717',
} as const;

/** Tons de estrutura usados no design (superfícies escuras e bordas). */
export const ink = {
  900: '#111111',
  800: '#1F1F1F',
  700: '#2D2D2D',
  600: '#3A3A3A',
  500: '#3F3F3F',
} as const;

/** Cores de feedback. O design usa apenas o vermelho de erro explicitamente. */
export const feedback = {
  success: '#2F855A',
  successDark: '#68D391',
  warning: '#B7791F',
  warningDark: '#F5B800',
  error: '#C0392B',
  errorDark: '#F87171',
  info: '#2B6CB0',
  infoDark: '#63B3ED',
} as const;

export const colors = {
  black: '#111111',
  white: '#FFFFFF',
  yellow,
  gray,
  ink,
  /** Alias para permitir colorScheme="brand" nos componentes do Chakra. */
  brand: yellow,
} as const;
