# Fonte do relatório — Desafio 4

Existem duas versões do relatório, cada uma com sua própria fonte:

- **Versão técnica** (`report_content.py` → `InsurMinds_Desafio4_Relatorio_Tecnico.*`):
  linguagem para quem já lê código, com tabelas de tools, tecnologias e
  tratamento de erro.
- **Versão simplificada** (`report_content_v2.py` →
  `InsurMinds_Desafio4_Relatorio_Simplificado.*`): reescrita em linguagem
  acessível, pensada para importar no Google Docs e para quem não programa.

Todo o conteúdo de cada versão vive em **um único lugar**: o respectivo
`report_content*.py` (capa + blocos de texto/tabelas/listas). Editar esse
arquivo é o jeito certo de:

- preencher o nome do grupo e os integrantes na capa (`COVER`);
- substituir os quatro `[PENDENTE — ...]` da seção "8. Exemplos de consultas"
  pelas respostas reais, depois de rodar a aplicação com uma `GROQ_API_KEY`
  válida e um dataset de teste.

## Como regenerar

Requer Python com `python-docx`, `reportlab`, `pypdf`, `matplotlib` e
`pillow` instalados (`pip install python-docx reportlab pypdf matplotlib
pillow`).

No PowerShell, a partir desta pasta:

```powershell
$base = ".."   # docs/desafio4
$env:REPORT_ASSETS_DIR = "$base\assets"
$env:REPORT_OUT_DOCX   = "$base\InsurMinds_Desafio4_Relatorio_Tecnico.docx"
$env:REPORT_OUT_PDF    = "$base\InsurMinds_Desafio4_Relatorio_Tecnico.pdf"
$env:REPORT_OUT_MD     = "$base\InsurMinds_Desafio4_Relatorio_Tecnico.md"

python make_diagram.py      # só se o diagrama (assets/arquitetura.png) mudar
python build_docx.py
python build_pdf.py
python export_markdown.py

# versão simplificada (Google Docs)
$env:REPORT_OUT_DOCX = "$base\InsurMinds_Desafio4_Relatorio_Simplificado.docx"
$env:REPORT_OUT_PDF  = "$base\InsurMinds_Desafio4_Relatorio_Simplificado_preview.pdf"
python make_diagram_v2.py   # só se o diagrama (assets/arquitetura_simples.png) mudar
python build_docx_v2.py
python build_pdf_v2.py      # PDF é só uma prévia rápida, não é a entrega
```

## Arquivos

| Arquivo | Papel |
| --- | --- |
| `report_content.py` | Fonte da versão técnica (capa + blocos). Editar aqui. |
| `make_diagram.py` | Gera `assets/arquitetura.png` (diagrama técnico). |
| `build_docx.py` | Renderiza a versão técnica em `.docx` (python-docx). |
| `build_pdf.py` | Renderiza a versão técnica em `.pdf` (reportlab). |
| `export_markdown.py` | Exporta a versão técnica em `.md` (leitura rápida / diff). |
| `report_content_v2.py` | Fonte da versão simplificada (capa + blocos). Editar aqui. |
| `make_diagram_v2.py` | Gera `assets/arquitetura_simples.png` (diagrama simplificado). |
| `build_docx_v2.py` | Renderiza a versão simplificada em `.docx`, pronta para o Google Docs. |
| `build_pdf_v2.py` | Gera um PDF de conferência rápida da versão simplificada. |

Para editar as perguntas e respostas ou a capa da versão simplificada, mexa
na lista `BLOCKS` e no dicionário `COVER` de `report_content_v2.py` e rode
`build_docx_v2.py` de novo.
