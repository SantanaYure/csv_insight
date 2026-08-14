import Papa from 'papaparse';

export interface ParsedCsv {
  headers: string[];
  rows: Record<string, string>[];
}

/**
 * Lê um CSV como texto. Detecta o delimitador automaticamente (vírgula ou
 * ponto e vírgula) e preserva os valores como texto — a conversão de tipos
 * acontece depois, com base no dicionário de dados.
 *
 * Roda em um Web Worker (`worker: true`) para não travar a aba em arquivos
 * grandes — exportações reais podem ter centenas de milhares de linhas, e
 * fazer isso na thread principal deixaria a interface completamente
 * congelada até o fim do parse. Se o worker não puder ser criado (CSP
 * restritiva, ambiente sem suporte), recai no modo síncrono.
 */
export function parseCsv(content: string): Promise<ParsedCsv> {
  const stripped = stripBom(content);

  return new Promise((resolve) => {
    try {
      Papa.parse<Record<string, string>>(stripped, {
        header: true,
        skipEmptyLines: 'greedy',
        transformHeader: (header) => header.trim(),
        worker: true,
        complete: (result) => resolve(toParsedCsv(result)),
      });
    } catch {
      resolve(toParsedCsv(parseSync(stripped)));
    }
  });
}

function parseSync(content: string): Papa.ParseResult<Record<string, string>> {
  return Papa.parse<Record<string, string>>(content, {
    header: true,
    skipEmptyLines: 'greedy',
    transformHeader: (header) => header.trim(),
  });
}

function toParsedCsv(result: Papa.ParseResult<Record<string, string>>): ParsedCsv {
  const headers = (result.meta.fields ?? []).filter((field) => field.length > 0);

  const rows = result.data
    .map((row) => {
      const normalized: Record<string, string> = {};
      headers.forEach((header) => {
        const value = row[header];
        normalized[header] = typeof value === 'string' ? value.trim() : '';
      });
      return normalized;
    })
    .filter((row) => headers.some((header) => row[header] !== ''));

  return { headers, rows };
}

function stripBom(content: string): string {
  return content.charCodeAt(0) === 0xfeff ? content.slice(1) : content;
}
