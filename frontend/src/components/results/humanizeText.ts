/**
 * Remove marcas de formatação que o resultado textual não interpreta e
 * referências técnicas que não ajudam na leitura da resposta.
 */
export function humanizeText(text: string): string {
  return text
    .replace(/\s*\(\s*coluna\s+[^()\n]{1,160}\)/gi, '')
    .replace(/\*\*(.*?)\*\*/gs, '$1')
    .replace(/__(.*?)__/gs, '$1')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/[ \t]+/g, ' ')
    .replace(/ *\n */g, '\n')
    .trim();
}
