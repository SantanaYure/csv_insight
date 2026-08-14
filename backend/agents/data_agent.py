"""Agente de análise de datasets usando Pydantic AI.

Este módulo declara o agente e suas tools. As regras de consulta continuam em
``services.dataset_service``; as tools apenas fornecem uma fronteira tipada e
escopada para o dataset da requisição atual.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, RunContext

from services.dataset_service import DatasetService, DatasetToolError


@dataclass(frozen=True)
class DatasetAgentDeps:
    """Dependências disponibilizadas ao agente durante uma análise."""

    dataset_id: str
    dataset_service: DatasetService


SYSTEM_INSTRUCTIONS = """Você é um analista de dados do CSV Insight.

Responda somente com base nos dados do dataset carregado nesta sessão e nas
informações retornadas pelas tools. Nunca use conhecimento geral para
completar uma resposta e nunca invente valores, totais, nomes ou tendências. O
dataset pode ter qualquer tema, tabela ou nome de coluna: não presuma que ele
seja de notas fiscais, compras ou fornecedores.

Use as tools sempre que precisar consultar dados. Escolha a menor consulta
necessária para responder à pergunta; não tente ler o ZIP bruto e não peça
nem reproduza o dataset inteiro. Se não houver dados suficientes ou se a
pergunta não tiver relação com o dataset, diga isso explicitamente. Seja
objetivo e responda em português do Brasil.

Escreva como uma pessoa analista falando com outra pessoa: use frases curtas,
naturais e claras. Prefira rótulos amigáveis, como "notas fiscais", "valor
total" e "fornecedor", quando o contexto permitir. Não mostre nomes técnicos
de colunas entre parênteses, a menos que o usuário peça explicitamente o nome
do campo. Em uma resposta simples, prefira: "O valor total das notas fiscais
é de R$ X." Evite frases como: "O valor total (coluna VALOR_NOTA) é **R$ X**."
Não use Markdown, asteriscos, crases, títulos ou introduções genéricas.
Entregue diretamente a resposta.
"""


def _delegate(call: Any) -> dict[str, Any]:
    """Converte falhas de domínio em um resultado que o agente pode explicar."""

    try:
        return call()
    except DatasetToolError as exc:
        return {"error": str(exc)}
    except (TypeError, ValueError):
        return {"error": "Parâmetros inválidos para esta consulta."}


def create_data_agent(model: Any) -> Agent[DatasetAgentDeps, str]:
    """Cria um agente configurado com as tools de consulta do dataset."""

    agent = Agent(
        model,
        output_type=str,
        deps_type=DatasetAgentDeps,
        instructions=SYSTEM_INSTRUCTIONS,
        retries=1,
        model_settings={
            "groq_reasoning_effort": "low",
            "groq_reasoning_format": "hidden",
        },
    )

    @agent.tool
    def listar_colunas(ctx: RunContext[DatasetAgentDeps], table: str | None = None) -> dict[str, Any]:
        """Lista as colunas de uma tabela ou de todas as tabelas do dataset."""

        return _delegate(lambda: ctx.deps.dataset_service.listar_colunas(ctx.deps.dataset_id, table))

    @agent.tool
    def obter_resumo(ctx: RunContext[DatasetAgentDeps]) -> dict[str, Any]:
        """Obtém nome, tabelas, totais de linhas e colunas do dataset."""

        return _delegate(lambda: ctx.deps.dataset_service.obter_resumo(ctx.deps.dataset_id))

    @agent.tool
    def buscar_registros(
        ctx: RunContext[DatasetAgentDeps], table: str, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        """Busca uma amostra paginada de até 10 registros de uma tabela."""

        return _delegate(
            lambda: ctx.deps.dataset_service.buscar_registros(
                ctx.deps.dataset_id, table, limit, offset
            )
        )

    @agent.tool
    def filtrar_dados(
        ctx: RunContext[DatasetAgentDeps],
        table: str,
        column: str,
        operator: str,
        value: str,
    ) -> dict[str, Any]:
        """Busca registros que atendem a uma condição sobre uma coluna."""

        return _delegate(
            lambda: ctx.deps.dataset_service.filtrar_dados(
                ctx.deps.dataset_id, table, column, operator, value
            )
        )

    @agent.tool
    def calcular_estatisticas(
        ctx: RunContext[DatasetAgentDeps], table: str, column: str
    ) -> dict[str, Any]:
        """Calcula estatísticas numéricas ou frequência de valores de uma coluna."""

        return _delegate(
            lambda: ctx.deps.dataset_service.calcular_estatisticas(
                ctx.deps.dataset_id, table, column
            )
        )

    return agent
