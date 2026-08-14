const numberFormatter = new Intl.NumberFormat('pt-BR');

/** 48721 -> "48.721". */
export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}
