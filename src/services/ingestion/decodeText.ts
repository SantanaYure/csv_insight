/**
 * Decodifica os bytes de um CSV tentando UTF-8 primeiro. Muitas exportações
 * de sistemas públicos brasileiros (ex.: portais de NF-e) usam
 * Windows-1252/ISO-8859-1: decodificá-las como UTF-8 transforma toda
 * acentuação em caracteres de substituição ("SÉRIE" -> "S�RIE"). Quando isso
 * é detectado, o texto é decodificado novamente como Windows-1252.
 */
export function decodeCsvBytes(bytes: Uint8Array): string {
  const utf8 = new TextDecoder('utf-8').decode(bytes);
  if (!hasReplacementChar(utf8)) return utf8;
  return new TextDecoder('windows-1252').decode(bytes);
}

function hasReplacementChar(text: string): boolean {
  return text.indexOf('�') !== -1;
}
