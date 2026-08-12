"""Ponto de integração isolado para o futuro agente de IA.

Nenhuma rota e nenhum outro serviço deve importar `MockAgentService`
diretamente — todos dependem apenas da interface `AgentService`. Trocar o
mock por um agente real (LLM, function calling, RAG sobre as tabelas etc.)
é uma questão de implementar essa interface em uma nova classe e apontar
`agent_service` (no fim do arquivo) para ela; nenhum contrato HTTP muda.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.models import AgentAnalyzeResponse, DatasetContext, TextQueryResult


class AgentService(ABC):
    """Interface pública conhecida pelo resto da aplicação."""

    @abstractmethod
    def analyze(
        self, question: str, dataset_context: DatasetContext | None = None
    ) -> AgentAnalyzeResponse:
        """Analisa `question` no contexto (opcional) de um dataset e
        devolve um `AgentAnalyzeResponse` com um `QueryResult` pronto para
        ser devolvido ao front-end."""
        raise NotImplementedError


class MockAgentService(AgentService):
    """Implementação provisória: respostas previsíveis, sem chamar nenhum
    modelo. Serve para o front-end ser desenvolvido/testado antes de existir
    um agente real."""

    SOURCE = "mock-agent"

    def analyze(
        self, question: str, dataset_context: DatasetContext | None = None
    ) -> AgentAnalyzeResponse:
        trimmed = question.strip()

        if not trimmed:
            return AgentAnalyzeResponse(
                status="error",
                source=self.SOURCE,
                result=TextQueryResult(
                    answer="Não foi possível entender a pergunta.",
                    detail="Envie uma pergunta com pelo menos um caractere.",
                ),
            )

        if dataset_context is not None:
            detail = (
                f"Dataset \"{dataset_context.datasetName}\" · "
                f"{len(dataset_context.tables)} tabela(s) "
                f"({', '.join(dataset_context.tables)}) · "
                f"{dataset_context.totalRows} linhas, {dataset_context.totalColumns} colunas."
            )
        else:
            detail = "Nenhum dataset foi informado para esta análise."

        return AgentAnalyzeResponse(
            status="success",
            source=self.SOURCE,
            result=TextQueryResult(
                answer=f'Análise simulada concluída para a pergunta: "{trimmed}".',
                detail=detail,
            ),
        )


agent_service: AgentService = MockAgentService()
