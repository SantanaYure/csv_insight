/**
 * Tipografia centralizada.
 *
 * A escala segue a tabela do design system: Display 48/36/32,
 * Título principal 36/30/28, Título de seção 28/24/22, Subtítulo 20/20/18,
 * Texto 16, Texto pequeno 14 e Legenda 12 (desktop / tablet / mobile).
 */
export const fonts = {
  heading: `Inter, system-ui, sans-serif`,
  body: `Inter, system-ui, sans-serif`,
  mono: `ui-monospace, SFMono-Regular, Menlo, monospace`,
};

export const fontWeights = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
};

export const fontSizes = {
  '2xs': '11px',
  xs: '12px',
  sm: '13px',
  'sm+': '13.5px',
  md: '14px',
  'md+': '14.5px',
  lg: '15px',
  'lg+': '15.5px',
  xl: '16px',
  '2xl': '17px',
  '3xl': '18px',
  '4xl': '20px',
  '5xl': '22px',
  '6xl': '24px',
  '7xl': '28px',
  '8xl': '32px',
  '9xl': '36px',
  display: '48px',
};

export const textStyles = {
  display: {
    fontSize: { base: '32px', md: '36px', lg: '48px' },
    lineHeight: 1.1,
    letterSpacing: '-0.02em',
    fontWeight: 700,
  },
  h1: {
    fontSize: { base: '28px', md: '30px', lg: '36px' },
    lineHeight: 1.15,
    letterSpacing: '-0.02em',
    fontWeight: 700,
  },
  h2: {
    fontSize: { base: '22px', md: '24px', lg: '28px' },
    lineHeight: 1.2,
    letterSpacing: '-0.01em',
    fontWeight: 700,
  },
  h3: {
    fontSize: { base: '17px', md: '18px' },
    lineHeight: 1.35,
    fontWeight: 600,
  },
  subtitle: {
    fontSize: { base: '18px', md: '20px' },
    lineHeight: 1.4,
    fontWeight: 600,
  },
  lead: {
    fontSize: { base: '16px', md: '17px', lg: '18px' },
    lineHeight: 1.6,
    fontWeight: 400,
  },
  body: {
    fontSize: '16px',
    lineHeight: 1.6,
    fontWeight: 400,
  },
  bodySm: {
    fontSize: '14px',
    lineHeight: 1.6,
    fontWeight: 400,
  },
  caption: {
    fontSize: '12px',
    lineHeight: 1.5,
    fontWeight: 500,
  },
  /** Rótulo em caixa alta usado em cards de estatística e títulos de grupo. */
  overline: {
    fontSize: '11px',
    fontWeight: 600,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
  },
  /** Cabeçalho de tabela. */
  tableHead: {
    fontSize: '11.5px',
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
} as const;
