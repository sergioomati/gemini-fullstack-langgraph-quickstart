from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


query_writer_instructions = """Seu objetivo é gerar consultas de busca web sofisticadas e diversificadas. Essas consultas são destinadas a uma ferramenta avançada de pesquisa web automatizada capaz de analisar resultados complexos, seguir links e sintetizar informações.

Instruções:
- Sempre prefira uma única consulta de busca, adicione apenas outra consulta se a pergunta original solicitar múltiplos aspectos ou elementos e uma consulta não for suficiente.
- Cada consulta deve focar em um aspecto específico da pergunta original.
- Não produza mais de {number_queries} consultas.
- As consultas devem ser diversificadas, se o tópico for amplo, gere mais de 1 consulta.
- Não gere múltiplas consultas similares, 1 é suficiente.
- A consulta deve garantir que as informações mais atuais sejam coletadas. A data atual é {current_date}.

Formato: 
- Formate sua resposta como um objeto JSON com TODAS essas três chaves exatas:
   - "rationale": Breve explicação de por que essas consultas são relevantes
   - "query": Uma lista de consultas de busca

Exemplo:

Tópico: Qual receita cresceu mais no ano passado, as ações da Apple ou o número de pessoas comprando um iPhone
```json
{{
    "rationale": "Para responder precisamente a esta questão comparativa de crescimento, precisamos de pontos de dados específicos sobre o desempenho das ações da Apple e métricas de vendas do iPhone. Essas consultas visam as informações financeiras precisas necessárias: tendências de receita da empresa, números de vendas unitárias específicos do produto e movimento do preço das ações no mesmo período fiscal para comparação direta.",
    "query": ["Crescimento da receita total da Apple ano fiscal 2024", "Crescimento das vendas unitárias do iPhone ano fiscal 2024", "Crescimento do preço das ações da Apple ano fiscal 2024"],
}}
```

Contexto: {research_topic}"""


web_searcher_instructions = """Conduza buscas direcionadas no Google para coletar as informações mais recentes e confiáveis sobre "{research_topic}" e sintetize-as em um artefato de texto verificável.

Instruções:
- A consulta deve garantir que as informações mais atuais sejam coletadas. A data atual é {current_date}.
- Conduza múltiplas buscas diversificadas para coletar informações abrangentes.
- Consolide os principais achados enquanto rastreia meticulosamente a(s) fonte(s) para cada informação específica.
- O resultado deve ser um resumo ou relatório bem escrito baseado em seus achados de busca.
- Inclua apenas as informações encontradas nos resultados de busca, não invente nenhuma informação.

Tópico de Pesquisa:
{research_topic}
"""

reflection_instructions = """Você é um assistente de pesquisa especialista analisando resumos sobre "{research_topic}".

Instruções:
- Identifique lacunas de conhecimento ou áreas que precisam de exploração mais profunda e gere uma consulta de acompanhamento. (1 ou múltiplas).
- Se os resumos fornecidos forem suficientes para responder à pergunta do usuário, não gere uma consulta de acompanhamento.
- Se houver uma lacuna de conhecimento, gere uma consulta de acompanhamento que ajudaria a expandir sua compreensão.
- Foque em detalhes técnicos, especificações de implementação ou tendências emergentes que não foram totalmente cobertas.

Requisitos:
- Garanta que a consulta de acompanhamento seja autocontida e inclua o contexto necessário para busca web.

Formato de Saída:
- Formate sua resposta como um objeto JSON com essas chaves exatas:
   - "is_sufficient": true or false
   - "knowledge_gap": Descreva que informação está faltando ou precisa de esclarecimento
   - "follow_up_queries": Escreva uma pergunta específica para abordar essa lacuna

Exemplo:
```json
{{
    "is_sufficient": true, // or false
    "knowledge_gap": "O resumo carece de informações sobre métricas de desempenho e benchmarks", // "" if is_sufficient is true
    "follow_up_queries": ["Quais são os benchmarks e métricas de desempenho típicos usados para avaliar [tecnologia específica]?"] // [] if is_sufficient is true
}}
```

Reflita cuidadosamente sobre os Resumos para identificar lacunas de conhecimento e produzir uma consulta de acompanhamento. Então, produza sua saída seguindo este formato JSON:

Resumos:
{summaries}
"""

answer_instructions = """Gere uma resposta de alta qualidade para a pergunta do usuário baseada nos resumos fornecidos.

Instruções:
- A data atual é {current_date}.
- Você é a etapa final de um processo de pesquisa em múltiplas etapas, não mencione que você é a etapa final.
- Você tem acesso a todas as informações coletadas das etapas anteriores.
- Você tem acesso à pergunta do usuário.
- Gere uma resposta de alta qualidade para a pergunta do usuário baseada nos resumos fornecidos e na pergunta do usuário.
- Você DEVE incluir todas as citações dos resumos na resposta corretamente.

Contexto do Usuário:
- {research_topic}

Resumos:
{summaries}"""
