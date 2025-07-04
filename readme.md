# LLM Chess Arena: Análise Comparativa de Modelos de Linguagem através do Xadrez como Benchmark Cognitivo

**Autor:** [Matheus Bernardes Costa do Nascimento](https://github.com/matheusbnas)  
**Orientador:** Leonardo Alfredo Forero Mendonza  
**Instituição:** Pontifícia Universidade Católica do Rio de Janeiro  

---

Trabalho apresentado ao curso [BI MASTER](https://ica.ele.puc-rio.br/) como pré-requisito para conclusão de curso e obtenção de crédito na disciplina "Projetos de Sistemas Inteligentes de Apoio à Decisão".

- **[Repositório no GitHub](https://github.com/matheusbnas/llm_chess_arena)**
- **[Dashboard Interativo](https://llm-chess-arena.streamlit.app)**

---

## Resumo

Este estudo desenvolveu uma plataforma inovadora para análise comparativa de modelos de linguagem de grande porte (LLMs) utilizando o xadrez como domínio de avaliação estratégica. A pesquisa demonstrou que diferentes modelos (GPT-4.1, GPT-4o, Gemini-2.5-Pro, Claude-4-Opus, Claude-4-Sonnet, DeepSeek-R1, DeepSeek-V3, Llama-3.3-70B) apresentam capacidades distintas de raciocínio tático e estratégico quando confrontados em partidas automatizadas. Os resultados revelaram que, embora LLMs não tenham sido projetados especificamente para jogar xadrez, sua performance neste domínio oferece insights valiosos sobre suas capacidades cognitivas gerais. O sistema desenvolvido incluiu torneios automatizados, análise em tempo real, integração com dados do Lichess.org via RAG, e um sistema de ranking ELO dinâmico. Os achados confirmaram que o xadrez serve como um benchmark eficaz para avaliar diferenças qualitativas entre modelos de IA, complementando métricas tradicionais de avaliação.

## Abstract

This study developed an innovative platform for comparative analysis of Large Language Models (LLMs) using chess as a strategic evaluation domain. The research demonstrated that different models (GPT-4.1, GPT-4o, Gemini-2.5-Pro, Claude-4-Opus, Claude-4-Sonnet, DeepSeek-R1, DeepSeek-V3, Llama-3.3-70B) exhibit distinct tactical and strategic reasoning capabilities when confronted in automated matches. Results revealed that although LLMs were not specifically designed to play chess, their performance in this domain provides valuable insights into their general cognitive capabilities. The developed system included automated tournaments, real-time analysis, Lichess.org data integration via RAG, and a dynamic ELO ranking system. The findings confirmed that chess serves as an effective benchmark for evaluating qualitative differences between AI models, complementing traditional evaluation metrics.

## 1. Introdução

### 1.1 A Era da IA e o Xadrez como Benchmark

A inteligência artificial no xadrez tem uma história rica que remonta ao **Deep Blue da IBM**, que em 1997 derrotou o campeão mundial Garry Kasparov, marcando um momento histórico na relação entre humanos e máquinas (CAMPBELL et al, 2002). O Deep Blue era um computador de xadrez criado pela IBM como parte de uma campanha publicitária. A empresa quis mostrar o poder de processamento de seu computador e organizou uma partida contra Kasparov, que era o campeão mundial na época. Este evento inaugurou uma nova era na avaliação de sistemas inteligentes através do xadrez.

Hoje, com o avanço dos modelos de linguagem de grande porte (LLMs), emerge uma nova fronteira: avaliar não engines especializados, mas sistemas de IA generalistas em domínios específicos. Os LLMs têm atingido bom desempenho na tarefa de processamento de texto em linguagem natural desde o início do emprego da arquitetura de Transformers (BROWN et al, 2020). Pesquisas recentes confirmam que LLMs não foram projetados para jogar xadrez especificamente, mas sua performance revela capacidades de raciocínio estratégico que transcendem o jogo em si (ACHER, 2024).

### 1.2 Motivação e Justificativa Científica

O desenvolvimento acelerado de LLMs criou uma demanda por métodos de avaliação que vão além de benchmarks tradicionais. O xadrez oferece um domínio ideal para esta análise por suas características únicas, e tem gerado interesse crescente na comunidade de pesquisa em IA (REDDIT LLMCHESS COMMUNITY, 2024):

- **Regras bem definidas**: Ambiente controlado para análise precisa
- **Complexidade estratégica**: Requer planejamento de longo prazo e análise posicional
- **Profundidade tática**: Demanda cálculo preciso e avaliação de consequências
- **Transparência**: Cada movimento pode ser analisado e compreendido
- **Reprodutibilidade**: Resultados podem ser verificados e replicados

Estudos precedentes demonstram que modelos como GPT-3.5-turbo-instruct podem atingir aproximadamente 1750 pontos ELO, mas ainda produzem movimentos ilegais em 16% das partidas, evidenciando tanto potencial quanto limitações importantes (ACHER, 2024).

### 1.3 Objetivos da Pesquisa

**Objetivo Principal**: Desenvolver e validar uma metodologia para análise comparativa de LLMs através de competições de xadrez automatizadas, fornecendo insights sobre capacidades cognitivas diferenciadas dos modelos.

**Objetivos Específicos**:
- Implementar sistema de torneios automatizados entre diferentes modelos de IA
- Desenvolver métricas específicas para avaliação de performance estratégica
- Integrar dados de alta qualidade do Lichess.org para aprimoramento via RAG
- Criar plataforma interativa para visualização e análise de resultados
- Estabelecer sistema de ranking ELO para classificação contínua dos modelos
- Avaliar impacto do sistema RAG na melhoria de performance

## 2. Fundamentação Teórica

### 2.1 LLMs e Limitações no Xadrez

A literatura científica estabelece claramente que LLMs como ChatGPT-4 e GPT-3.5-turbo apresentam limitações significativas para jogar xadrez, com altas taxas de movimentos ilegais (ACHER, 2024). Embora sejam poderosos e capazes de gerar texto de maneira rápida e coerente, ainda há riscos e fragilidades em usar os LLMs para geração de conteúdo especializado. Estudos controlados revelam que:

- **GPT-4 (Chat)**: ~30% de partidas com movimentos ilegais
- **GPT-3.5-turbo-instruct**: ~16% de partidas com movimentos ilegais  
- **Modelos de chat vs. completion**: Ajuste fino para conversação degrada performance no xadrez (ACHER, 2024)

### 2.2 Engines de Xadrez vs. LLMs

É fundamental distinguir entre engines de xadrez especializados e LLMs generalistas. Engines como Stockfish atingem ratings superiores a 3000 pontos ELO, enquanto os melhores LLMs alcançam aproximadamente 1750-1800 ELO (CHESS.COM, 2024; ACHER, 2024). Esta diferença não representa uma falha dos LLMs, mas sim evidencia que seu valor reside na versatilidade e capacidade de raciocínio geral, não na especialização.

As engines de xadrez são muito mais fortes que os humanos, com as melhores alcançando um rating estimado de mais de 3000 pontos. As engines também estão ficando mais fortes a cada ano devido a melhorias em hardware e software. O AlphaZero, por exemplo, introduziu o conceito de redes neurais no mundo do xadrez (SILVER et al, 2016). Todas as engines mais potentes adotaram esse tipo de ferramenta de processamento de informações e se tornaram ainda mais poderosas.

### 2.3 Xadrez como Proxy para Capacidades Cognitivas

O xadrez serve como um "proxy" para avaliar:
- **Raciocínio estratégico**: Planejamento de longo prazo
- **Análise tática**: Cálculo de sequências complexas
- **Reconhecimento de padrões**: Identificação de estruturas posicionais
- **Tomada de decisão**: Avaliação de riscos e recompensas
- **Adaptabilidade**: Resposta a situações emergentes

## 3. Metodologia

### 3.1 Arquitetura do Sistema

O projeto implementou uma arquitetura modular baseada em:

```
Frontend: Streamlit + Visualizações Interativas
├── Dashboard de Resultados
├── Sistema de Torneios
├── Análise de Partidas
└── Rankings ELO Dinâmicos

Backend: Python + Motor de Xadrez
├── API de Integração Multi-LLM
├── Sistema de Análise (python-chess)
├── Processamento PGN
└── Banco de Dados SQLite

Integrações:
├── OpenAI (GPT-4.1, GPT-4o, GPT-3.5-turbo)
├── Google AI (Gemini-2.5-Pro, Gemini-2.5-Flash)
├── Anthropic (Claude-4-Opus, Claude-4-Sonnet)
├── DeepSeek (DeepSeek-R1, DeepSeek-V3)
├── Groq (Llama-3.3-70B, Llama-3.1-8B)
└── Lichess API (dados RAG)
```

### 3.2 Modelos Avaliados

| Modelo | Provedor | Especialização | Status |
|--------|----------|----------------|--------|
| **GPT-4.1** | OpenAI | Raciocínio multimodal avançado | Ativo |
| **GPT-4o** | OpenAI | Otimizado para conversação | Ativo |
| **Gemini-2.5-Pro** | Google | Processamento multimodal | Ativo |
| **Gemini-2.5-Flash** | Google | Velocidade otimizada | Ativo |
| **Claude-4-Opus** | Anthropic | Precisão e segurança máxima | Ativo |
| **Claude-4-Sonnet** | Anthropic | Equilibrado | Ativo |
| **DeepSeek-R1** | DeepSeek | Raciocínio avançado | Ativo |
| **DeepSeek-V3** | DeepSeek | Propósito geral | Ativo |
| **Llama-3.3-70B** | Groq | Inferência rápida | Ativo |

Os modelos GPT são uma família de LLMs desenvolvidos e disponibilizados pela OpenAI em diversas configurações e versões diferentes (OPENAI TEAM, 2024). O modelo Gemini representa uma família de modelos multimodais altamente capazes desenvolvidos pelo Google (GOOGLE DEEPMIND, 2024). A família Claude 4 representa a mais recente geração de modelos da Anthropic, combinando capacidades avançadas com foco em segurança (ANTHROPIC, 2024).

### 3.3 Métricas de Avaliação

**Métricas Primárias**:
- **Rating ELO**: Sistema clássico de classificação adaptado
- **Taxa de Legalidade**: Porcentagem de movimentos válidos
- **Tempo de Resposta**: Eficiência de tomada de decisão
- **Qualidade Estratégica**: Análise de padrões posicionais

**Métricas Secundárias**:
- **Performance por Abertura**: Especialização em tipos de jogo
- **Consistência Temporal**: Estabilidade de performance
- **Adaptabilidade**: Resposta a estilos adversários

### 3.4 Sistema RAG Integrado

Implementação de Retrieval-Augmented Generation usando dados de alta qualidade. A estrutura RAG (Retrieval Augmented Generation) tem sido aplicada para contornar limitações dos LLMs. Ela consiste em acoplar um modelo de busca (retrieval) a um modelo generativo, de modo a melhorar o processo de geração por meio das informações encontradas pelo buscador (LICHESS.ORG, 2024):

- **Fonte de Dados**: Partidas de mestres do Lichess (>2500 ELO)
- **Processamento**: Extração de padrões estratégicos
- **Integração**: Enriquecimento contextual de prompts
- **Validação**: Métricas de melhoria de performance

## 4. Resultados e Análises

### 4.1 Performance Geral dos Modelos

Os resultados preliminares demonstraram diferenças significativas entre os modelos testados:

| Modelo | Taxa de Legalidade (%) | Tempo Médio (s) | Observações |
|--------|------------------------|------------------|-------------|
| **Claude-4-Opus** | 85-90% | 2.1 | Melhor compreensão estratégica |
| **GPT-4.1** | 80-85% | 1.8 | Bom raciocínio tático |
| **DeepSeek-R1** | 82-87% | 2.4 | Excelente em cálculos |
| **Gemini-2.5-Pro** | 78-83% | 1.9 | Adaptabilidade notável |
| **Llama-3.3-70B** | 75-80% | 1.2 | Muito rápido |

*Nota: Os valores apresentados são baseados em testes preliminares e podem variar conforme configurações específicas do prompt e contexto da partida.*

### 4.2 Análise por Tipo de Abertura

Diferentes modelos demonstraram especializações em aberturas específicas:

**Aberturas Abertas (1.e4)**:
- Claude-4-Opus apresentou superioridade técnica
- Melhor compreensão de táticas agudas

**Aberturas Fechadas (1.d4)**:
- DeepSeek-R1 demonstrou melhor jogo posicional
- Maior precisão em estruturas complexas

**Gambitos e Aberturas Irregulares**:
- Resultados mais equilibrados entre todos os modelos
- GPT-4.1 mostrou maior adaptabilidade

### 4.3 Impacto do Sistema RAG

A integração do sistema RAG produziu melhorias mensuráveis:

**Melhorias Observadas**:
- **Precisão Geral**: +2-4% em média nos testes
- **Qualidade de Abertura**: +8-15% nas primeiras 10 jogadas
- **Tempo de Decisão**: -10-20% de redução
- **Consistência**: Menor variação entre partidas

**Análise Qualitativa**:
- Maior coerência estratégica em posições complexas
- Melhor reconhecimento de padrões clássicos
- Redução de erros táticos elementares

### 4.4 Taxa de Movimentos Ilegais

Confirmando a literatura, observou-se variação significativa:

| Categoria de Modelo | Taxa de Ilegalidade | Principal Causa |
|---------------------|-------------------|-----------------|
| Modelos de Raciocínio (DeepSeek-R1, Claude-4) | 10-15% | Complexidade posicional |
| Modelos Generalistas (GPT-4.1, Gemini-2.5) | 15-20% | Regras específicas |
| Modelos Rápidos (Llama-3.3) | 20-25% | Tempo limitado de análise |

**Observação Importante**: Essas limitações não invalidam a utilidade dos LLMs, mas sim evidenciam a necessidade de sistemas auxiliares para aplicações críticas. Como observado em estudos precedentes, mesmo os melhores modelos ainda fazem movimentos ilegais, sugerindo que o sistema não é completamente capaz de induzir todas as regras do xadrez (ACHER, 2024).

## 5. Contribuições Científicas

### 5.1 Metodologia Inovadora

1. **Primeira plataforma** dedicada à análise sistemática de LLMs via xadrez
2. **Framework reproduzível** para avaliação comparativa de modelos
3. **Métricas específicas** para capacidades estratégicas
4. **Sistema RAG** otimizado para domínio especializado

### 5.2 Insights sobre Capacidades dos LLMs

**Descobertas Principais**:
- LLMs demonstram estilos de jogo distintos e identificáveis
- Performance no xadrez correlaciona com capacidades de raciocínio geral
- Modelos especializados em raciocínio (DeepSeek-R1) não necessariamente superam generalistas em todos os aspectos
- RAG melhora performance mas não elimina limitações fundamentais

### 5.3 Implicações para Desenvolvimento de IA

Os resultados sugerem que:
- **Benchmarks tradicionais** podem não capturar diferenças qualitativas importantes
- **Avaliação em domínios específicos** oferece insights complementares valiosos
- **Especialização vs. generalização** representa trade-off fundamental em LLMs
- **Sistemas híbridos** (LLM + ferramentas especializadas) são mais promissores que modelos isolados

## 6. Limitações e Trabalhos Futuros

### 6.1 Limitações do Estudo

- **Amostra limitada**: Número restrito de partidas por limitações orçamentárias
- **Variabilidade de prompts**: Engenharia de prompts não completamente otimizada
- **Modelos específicos**: Análise limitada a versões específicas dos LLMs
- **Ausência de engine de avaliação**: Não foi utilizado Stockfish para validação objetiva dos movimentos

### 6.2 Extensões Futuras

**Técnicas Avançadas**:
- **Integração com Stockfish**: Implementar engine de xadrez profissional para avaliação objetiva da qualidade dos movimentos, classificando-os como excelentes, bons, imprecisos, erros ou blunders
- **Análise de profundidade**: Usar Stockfish para calcular variações táticas e comparar com as escolhas dos LLMs
- **Sistema de pontuação híbrido**: Combinar ELO tradicional com métricas de qualidade baseadas em engine

**Modelos e Técnicas**:
- Integração com mais modelos (LLaMA, Mistral, Claude-3.5-Sonnet, etc.)
- Otimização avançada de prompts com few-shot learning
- Análise temporal da evolução dos modelos
- Implementação de fine-tuning especializado para xadrez

**Aplicações Expandidas**:
- Extensão para outros jogos estratégicos (Go, Poker, Damas)
- Análise de capacidades criativas em composições de xadrez
- Avaliação de raciocínio matemático através de puzzles táticos
- Benchmarks para tomada de decisão empresarial baseados em princípios estratégicos

**Melhorias no Sistema**:
- Interface web mais avançada com análise em tempo real
- Sistema de torneios com múltiplas rodadas e formatos
- Integração com plataformas online como Chess.com e Lichess
- Desenvolvimento de API pública para pesquisadores

## 7. Conclusões

### 7.1 Síntese dos Achados

Esta pesquisa estabeleceu o xadrez como um benchmark válido e revelador para análise comparativa de LLMs. Os resultados confirmaram que, embora esses modelos não tenham sido projetados para jogar xadrez, sua performance neste domínio oferece insights únicos sobre suas capacidades cognitivas diferenciadas.

**Principais Conclusões**:

1. **Diversidade de Capacidades**: Diferentes LLMs demonstram especializações estratégicas distintas, validando a necessidade de múltiplas abordagens de avaliação

2. **Limitações Fundamentais**: A persistência de movimentos ilegais (10-25%) evidencia que LLMs requerem sistemas auxiliares para aplicações críticas, confirmando observações da literatura sobre a incapacidade dos modelos de induzir completamente as regras do domínio (ACHER, 2024)

3. **Eficácia do RAG**: O sistema desenvolvido demonstrou melhorias consistentes, validando a abordagem de augmentação via recuperação para aprimoramento de LLMs em domínios específicos

4. **Benchmark Complementar**: O xadrez provou ser um complemento valioso aos benchmarks tradicionais, revelando aspectos qualitativos não capturados por métricas convencionais

### 7.2 Impacto e Relevância

**Para a Comunidade Científica**:
- Nova metodologia de avaliação de LLMs
- Framework open-source para pesquisas futuras  
- Dados empíricos sobre capacidades estratégicas de modelos atuais
- Evidências sobre degradação de performance em modelos ajustados para chat (ACHER, 2024)

**Para a Indústria**:
- Insights para seleção de modelos em aplicações específicas
- Validação da importância de sistemas híbridos
- Métricas para desenvolvimento de produtos baseados em IA

**Para Educação**:
- Ferramenta pedagógica para ensino de IA
- Demonstração prática de capacidades e limitações de LLMs
- Plataforma para experimentação acadêmica

### 7.3 Perspectiva Final

O estudo demonstra que o valor dos LLMs não reside em superar engines especializados, mas em oferecer capacidades de raciocínio geral aplicáveis a domínios diversos. O xadrez, como microcosmo de tomada de decisão estratégica, fornece uma janela única para compreender e comparar essas capacidades emergentes. Como evidenciado pela evolução desde o Deep Blue até os engines modernos como Stockfish e AlphaZero, a especialização em xadrez atingiu níveis sobre-humanos (CAMPBELL et al, 2002; SILVER et al, 2016), mas os LLMs representam uma abordagem fundamentalmente diferente focada na versatilidade cognitiva (BROWN et al, 2020).

A plataforma desenvolvida representa tanto um resultado científico quanto uma ferramenta para pesquisas futuras, contribuindo para o avanço da compreensão sobre inteligência artificial generalista na era dos grandes modelos de linguagem. A incorporação futura de engines como Stockfish promete elevar significativamente a qualidade das análises, permitindo validação objetiva das capacidades estratégicas dos LLMs.

---

## Referências

1. **Acher, M.** (2024). "Debunking the Chessboard: Confronting GPTs Against Chess Engines to Estimate Elo Ratings and Assess Legal Move Abilities". *arXiv preprint arXiv:2408.08781*.

2. **Anthropic.** (2024). "Claude 4 Model Family: Capabilities and Safety". *Technical Report*.

3. **Brown, T.** et al. (2020). "Language Models are Few-Shot Learners". *Advances in Neural Information Processing Systems*, 33, 1877-1901.

4. **Campbell, M.** et al. (2002). "Deep Blue". *Artificial Intelligence*, 134(1-2), 57-83.

5. **Chess.com.** (2024). "Engine de Xadrez - Definição e História". Disponível em: https://www.chess.com/pt-BR/terms/engine-xadrez

6. **Google DeepMind.** (2024). "Gemini 2.0: Our new AI model for the agentic era". *Google AI Blog*. Disponível em: https://blog.google/technology/google-deepmind/google-gemini-ai-update-december-2024/

7. **Lichess.org.** (2024). "Lichess API Documentation". Disponível em: https://lichess.org/api

8. **OpenAI Team.** (2024). "GPT-4 and GPT-4 Turbo". *OpenAI Documentation*. Disponível em: https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo

9. **Reddit LLMChess Community.** (2024). "Discussions on LLM Chess Performance". Disponível em: https://www.reddit.com/r/LLMChess/

10. **Silver, D.** et al. (2016). "Mastering the game of Go with deep neural networks and tree search". *Nature*, 529(7587), 484-489.

11. **Stockfish Team.** (2024). "Stockfish Chess Engine". Disponível em: https://stockfishchess.org/

12. **Vaswani, A.** et al. (2017). "Attention is All You Need". *Advances in Neural Information Processing Systems*, 30, 5998-6008.

---

## Informações do Projeto

**Matrícula**: 222.100.459  

**Instituição**: Pontifícia Universidade Católica do Rio de Janeiro 

**Curso**: Pós-Graduação Business Intelligence Master  

**Data de Submissão**: Julho 2025