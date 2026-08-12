import { feedback } from './colors';

/**
 * Tokens semânticos. Cada entrada declara o valor do modo claro em `default`
 * e o do modo escuro em `_dark`, exatamente como os pares de variáveis CSS
 * definidos no design original.
 */
export const semanticTokens = {
  colors: {
    'background.page': { default: '#FAFAFA', _dark: '#111111' },
    'background.surface': { default: '#FFFFFF', _dark: '#1F1F1F' },
    'background.subtle': { default: '#F5F5F5', _dark: '#2A2A2A' },
    'background.inverse': { default: '#111111', _dark: '#1F1F1F' },
    'background.header': {
      default: 'rgba(255,255,255,.88)',
      _dark: 'rgba(17,17,17,.9)',
    },
    'background.overlay': {
      default: 'rgba(17,17,17,.5)',
      _dark: 'rgba(0,0,0,.62)',
    },

    'text.primary': { default: '#111111', _dark: '#FFFFFF' },
    'text.secondary': { default: '#444444', _dark: '#D4D4D4' },
    'text.muted': { default: '#7A7A7A', _dark: '#A3A3A3' },
    'text.inverse': { default: '#FFFFFF', _dark: '#111111' },
    'text.onInverse': { default: '#FFFFFF', _dark: '#FFFFFF' },
    'text.onInverseMuted': { default: '#B5B5B5', _dark: '#B5B5B5' },

    'border.default': { default: '#E5E5E5', _dark: '#2D2D2D' },
    'border.strong': { default: '#D9D9D9', _dark: '#3A3A3A' },
    'border.contrast': { default: '#2D2D2D', _dark: '#3F3F3F' },

    'brand.primary': { default: '#FFCA28', _dark: '#FFCA28' },
    'brand.primaryHover': { default: '#F5B800', _dark: '#FFD84D' },
    'brand.primaryActive': { default: '#D99D00', _dark: '#F5B800' },
    'brand.soft': { default: '#FFF3BF', _dark: '#3A3115' },
    'brand.tint': { default: '#FFFBEA', _dark: '#221E13' },
    'brand.textOnPrimary': { default: '#111111', _dark: '#111111' },

    'chat.userBg': { default: '#111111', _dark: '#FFCA28' },
    'chat.userText': { default: '#FFFFFF', _dark: '#111111' },

    'chart.grid': { default: '#EEEEEE', _dark: '#2A2A2A' },
    'chart.axis': { default: '#7A7A7A', _dark: '#A3A3A3' },

    'feedback.success': { default: feedback.success, _dark: feedback.successDark },
    'feedback.warning': { default: feedback.warning, _dark: feedback.warningDark },
    'feedback.error': { default: feedback.error, _dark: feedback.errorDark },
    'feedback.info': { default: feedback.info, _dark: feedback.infoDark },
  },
  shadows: {
    /** Sombra discreta de card: 0 1px 2px. */
    card: {
      default: '0 1px 2px rgba(17,17,17,.05)',
      _dark: '0 1px 2px rgba(0,0,0,.45)',
    },
    /** Sombra da bolha de resposta do agente. */
    bubble: {
      default: '0 1px 3px rgba(17,17,17,.05)',
      _dark: '0 1px 3px rgba(0,0,0,.45)',
    },
    /** Sombra de destaque (preview do hero, painel do 404). */
    floating: {
      default: '0 12px 40px rgba(17,17,17,.06)',
      _dark: '0 12px 40px rgba(0,0,0,.45)',
    },
    /** Sombra de diálogo. */
    dialog: {
      default: '0 24px 60px rgba(0,0,0,.28)',
      _dark: '0 24px 60px rgba(0,0,0,.55)',
    },
  },
} as const;
