# Contribuições e Autoavaliação

**Trabalho 1 — Redes de Computadores | ICT/UNIFESP**

> Divisão **arbitrária e equilibrada** das atividades, cobrindo todo o ciclo do
> projeto: do planejamento à análise de resultados. Ajuste os nomes e, se
> quiser, redistribua os itens conforme o que cada um de fato fez.

## Divisão de atividades (ciclo completo)

### Pedro Henrique Novello D'Elia Porto de Almeida — Aplicação (servidor)
- **Planejamento:** definição do protocolo (inspirado em HTTP) e dos códigos de
  status; estrutura de arquivos do projeto.
- **Implementação — servidor:** `server.c` (modelo thread-por-cliente com
  `pthread`), `handle_get`/`handle_put`, tratamento de erros (400/403/404/500),
  proteção contra path traversal.
- **Implementação — comum:** `common.c` (`send_all`/`recv_all`/`recv_file`).

### Lucas Alves Gazale — Aplicação (cliente) e análise
- **Implementação — cliente:** `client.c` (GET/PUT, medição de tempo com
  `CLOCK_MONOTONIC`, telemetria em CSV).
- **Análise:** `analyze.py` (estatística descritiva + intervalo de confiança) e
  geração dos gráficos (tempo, vazão, boxplot, CDF).
- **Comunicação:** slides da apresentação.

### Henrique Rodrigues Ribeiro — Ambiente e experimentos
- **Ambiente experimental:** montagem da VM (Vagrant/VirtualBox), Docker e
  imagem do CORE; topologia em `topologia_core.py` (acesso + núcleo + gargalo).
- **Execução e validação:** scripts `gen_files.sh` e `run_experiment.sh`;
  rodadas 4G e Fibra (n=15 por configuração), coleta dos CSVs; verificação de
  consistência com ping/traceroute/iperf.
- **Comunicação:** documentação (`RELATORIO.md`, `GUIA_DISCUSSAO.md`) e roteiro
  do vídeo.

> A lógica da divisão: **dois integrantes na aplicação em C** (um no servidor,
> outro no cliente) e **um responsável pelo ambiente/experimentos de ponta a
> ponta** — quem montou o CORE é quem rodou os testes nele. A análise/gráficos e
> a documentação foram distribuídas entre os dois que tiveram frentes mais
> curtas de código, equilibrando a carga.

> **Observação importante:** embora cada integrante tenha tido um **foco
> principal**, todas as decisões de projeto (protocolo, fatores experimentais,
> interpretação dos resultados) foram discutidas e tomadas **em conjunto**. A
> divisão acima reflete a responsabilidade principal de cada um, não um trabalho
> isolado.

## Autoavaliação do grupo

- **Requisitos:** atendemos a todos — aplicação em C com GET/PUT, servidor
  concorrente (múltiplos clientes simultâneos), topologia com redes de acesso e
  núcleo, enlace gargalo configurado e validado, experimentos com repetições e
  análise estatística com gráficos.
- **Qualidade dos resultados:** os dados se mostraram **fisicamente coerentes**
  — a vazão agregada se aproxima da banda configurada no gargalo (20 Mbps no 4G,
  ~100 Mbps na Fibra) e o RTT medido corresponde a ~2× o atraso do enlace. Essa
  consistência nos deu confiança de que tanto a implementação quanto o ambiente
  emulado estavam corretos.
- **Maior desafio:** montar o ambiente CORE numa VM *headless* (sem interface
  gráfica). Resolvemos automatizando a criação da topologia e dos experimentos
  por um script Python usando a API do CORE — o que, além de contornar a falta
  de GUI, tornou o experimento **reprodutível**.
- **Principal aprendizado:** entender como **latência** e **largura de banda**
  dominam regimes diferentes (arquivos pequenos vs. grandes) e observar na
  prática o fenômeno de **saturação** do enlace sob concorrência.
- **Nota que o grupo atribui ao próprio trabalho:** **[preencher — ex.: 9,5/10]**,
  justificada pelo cumprimento integral dos requisitos e pela coerência dos
  resultados.

## Checklist antes de gravar/entregar
- [ ] Substituir `[Integrante 1/2/3]` pelos nomes reais (aqui, no slide 17 e no slide 1).
- [ ] Revisar se a divisão reflete o que cada um fez (ajustar se necessário).
- [ ] Definir a nota da autoavaliação.
