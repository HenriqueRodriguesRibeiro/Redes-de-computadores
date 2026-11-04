# Relatório — Avaliação de Desempenho de Cliente-Servidor de Arquivos

**UC Redes de Computadores — ICT/UNIFESP**
Trabalho 1 | Prazo: 05/11/2026

Este documento descreve **o que** foi desenvolvido, **como** foi desenvolvido e
**por que** cada decisão foi tomada. Serve de roteiro para o tópico
"O trabalho desenvolvido (o que, como e porque)" do vídeo-relatório.

---

## 1. Introdução e motivação

Transferir arquivos pela rede é uma das operações mais comuns da Internet:
carregar uma página web, baixar uma foto, enviar um vídeo. O **desempenho**
dessa transferência (quão rápido e com qual vazão) depende de vários fatores:
o tamanho do arquivo, quantos usuários disputam o servidor ao mesmo tempo, e
as características do enlace de rede (largura de banda e latência).

**Problema abordado:** como esses fatores afetam o tempo de resposta e a vazão
de uma aplicação cliente-servidor de arquivos? Onde estão os gargalos e os
pontos de saturação?

Para responder, implementamos uma aplicação cliente-servidor de arquivos em C
(com a API de Sockets) e a avaliamos de forma controlada em uma topologia de
rede emulada no CORE, variando sistematicamente os fatores de interesse.

---

## 2. O QUE foi desenvolvido

### 2.1 Aplicação cliente-servidor em C

Uma aplicação de transferência de arquivos com protocolo próprio inspirado no
HTTP, suportando duas operações:

- **GET** — o cliente baixa um arquivo do servidor (substitui o local, se existir).
- **PUT** — o cliente envia um arquivo para o servidor (substitui o remoto, se existir).

O servidor é **concorrente**: atende múltiplos clientes simultaneamente, cada um
em sua própria *thread* (POSIX `pthread`). Em caso de erro, responde com o código
apropriado (inspirado no HTTP): `200 OK`, `201 CREATED`, `400 BAD REQUEST`,
`403 FORBIDDEN`, `404 NOT FOUND`, `500 INTERNAL ERROR`.

### 2.2 Ambiente experimental emulado (CORE)

Uma topologia de rede com **redes de acesso** e **núcleo**:

```
[servidor] --(acesso A)-- R1 ==(NÚCLEO / gargalo)== R2 --(acesso B)-- [cliente]
```

Um dos enlaces do núcleo (R1↔R2) é o **gargalo**, onde configuramos banda e
latência para emular diferentes tecnologias de acesso.

### 2.3 Automação e análise

Scripts que geram os arquivos de teste, executam o grid completo de experimentos
(com repetições) coletando telemetria em CSV, e processam os dados gerando
estatísticas e gráficos.

---

## 3. COMO foi desenvolvido

### 3.1 Protocolo da aplicação

Escolhemos um protocolo textual simples, **inspirado no HTTP**, por ser familiar,
fácil de depurar e suficiente para o objetivo (não era requisito reimplementar
HTTP completo).

**Requisição GET:**
```
GET <caminho>\r\n
\r\n
```
**Resposta GET (sucesso):**
```
200 OK\r\n
LENGTH: <bytes>\r\n
\r\n
<conteúdo do arquivo>
```
**Requisição PUT:** envia cabeçalho com `LENGTH:` e, em seguida, os bytes.
**Resposta PUT:** `201 CREATED` (ou código de erro).

O campo `LENGTH` é essencial: como o TCP é um **fluxo contínuo de bytes** (não
preserva fronteiras de mensagem), o receptor precisa saber exatamente quantos
bytes ler para delimitar o arquivo.

### 3.2 Servidor concorrente (uma thread por cliente)

**Por quê threads?** O requisito central é atender **múltiplos clientes
simultaneamente**. Adotamos o modelo *thread-por-conexão* com `pthread`:
o laço principal faz `accept()` e, a cada nova conexão, cria uma thread
(`pthread_create` + `pthread_detach`) que trata aquele cliente de forma isolada.

**Vantagens para este trabalho:**
- Simples de entender e implementar corretamente.
- Permite que transferências lentas (arquivo grande / rede lenta) de um cliente
  **não bloqueiem** os demais — cada um progride em paralelo.
- É exatamente o modelo que expõe o fenômeno que queremos medir: a **disputa**
  por um recurso compartilhado (a banda do gargalo) quando a concorrência cresce.

**Robustez implementada:**
- `send_all` / `recv_all`: repetem o envio/recebimento até transferir **todos**
  os bytes (um único `send`/`recv` pode transferir só parte dos dados).
- `SIGPIPE` ignorado: se um cliente desconecta no meio, o servidor não é
  derrubado — a thread apenas trata o erro.
- Proteção contra *path traversal* (rejeita caminhos com `..`).
- Uso de `snprintf`/`strncpy` para evitar estouro de buffer.

### 3.3 Cliente com telemetria

O cliente executa GET ou PUT e **mede** o tempo de resposta com
`clock_gettime(CLOCK_MONOTONIC)` — um relógio monotônico, imune a ajustes de
hora do sistema, ideal para medir intervalos com precisão. Calcula a vazão
(`bytes × 8 / tempo`, em Mbps) e registra tudo em CSV, com uma *tag* que
identifica a tecnologia, o arquivo, a concorrência e a repetição.

### 3.4 Topologia no CORE — por script Python (sem GUI)

Montamos a topologia pela **API Python do CORE**, não pela interface gráfica.

**Por quê sem GUI?** O ambiente é uma VM Linux *headless* (acessada por SSH),
sem servidor gráfico. Montar a topologia por script traz vantagens:
- **Reprodutibilidade:** a topologia é sempre idêntica, descrita em código.
- **Automação:** o mesmo script configura o gargalo, valida a rede e dispara
  os experimentos de ponta a ponta.
- O requisito do enunciado é *ter* a topologia (acesso + núcleo + gargalo
  validado), e não necessariamente montá-la por cliques — o resultado é
  equivalente.

**Validação da consistência (requisito 2.1):** antes dos experimentos,
confirmamos que os parâmetros configurados se refletem de fato na emulação:
- `ping` — RTT fim-a-fim (deve ser ~2× o atraso do gargalo).
- `traceroute` — RTT por salto (o salto do núcleo concentra a latência).
- `iperf` — vazão (próxima da banda configurada no gargalo).

### 3.5 Metodologia experimental

Para cada combinação de fatores, repetimos o experimento **n = 15 vezes**
(o enunciado pede n > 10; em ambiente controlado a variação converge rápido).
Coletamos **tempo de resposta** e **vazão** de cada operação.

---

## 4. POR QUE cada escolha de fator

O plano experimental cruza 4 fatores. A escolha de cada um:

### 4.1 Tamanho do arquivo — ~100 KB e ~10 MB
Representam **duas aplicações típicas da Internet**:
- **~100 KB** — uma página web (HTML + CSS + imagens pequenas). Transferência
  curta, dominada pela **latência** (tempo de ida-e-volta, estabelecimento).
- **~10 MB** — uma foto em alta resolução ou um vídeo curto. Transferência
  longa, dominada pela **largura de banda** (vazão sustentada).

Esse contraste permite observar como o gargalo afeta cada regime de forma
diferente.

### 4.2 Operação — GET e PUT
As duas operações da aplicação. Interessa comparar o comportamento de
**download** (GET) e **upload** (PUT), que podem ter desempenho distinto
dependendo da direção do tráfego e do padrão de leitura/escrita.

### 4.3 Concorrência — 1, 10 e 50 clientes
Cenários de **baixa, média e alta** escala de uso:
- **1 cliente** — linha de base, sem disputa.
- **10 clientes** — carga moderada.
- **50 clientes** — alta carga, para evidenciar **saturação** e a divisão da
  banda do gargalo entre os clientes.

### 4.4 Tecnologia de rede no gargalo — 4G/LTE e Fibra
Duas **tecnologias comuns de acesso à Internet**, com parâmetros típicos:
- **4G/LTE** — ~20 Mbps / ~50 ms (banda menor, latência maior).
- **Fibra** — ~100 Mbps / ~5 ms (banda maior, latência menor).

O contraste mostra o impacto da **banda** (arquivos grandes) e da **latência**
(arquivos pequenos) no desempenho.

> **Total:** 2 arquivos × 2 operações × 3 concorrências × 2 tecnologias =
> **24 configurações** × 15 repetições = **360 execuções** (× nº de clientes
> por rodada na coleta por cliente).

---

## 5. COMO os resultados são analisados

A partir do CSV coletado, calculamos **estatística descritiva** por configuração:
- média, mediana, desvio padrão e **intervalo de confiança de 95%** do tempo de
  resposta;
- vazão média.

E geramos **gráficos** para interpretação:
- **Barras / linhas com IC** — tempo médio × concorrência, por tecnologia/operação.
- **Boxplot** — distribuição do tempo de resposta (dispersão e *outliers*).
- **CDF** — probabilidade acumulada do tempo (útil para percentis, ex.: p95).
- **Vazão × concorrência** — identifica o ponto de saturação da banda.

Com isso, identificamos **gargalos** (onde o desempenho degrada) e **pontos de
saturação** (a partir de quantos clientes a vazão por cliente deixa de crescer
porque a banda do gargalo está totalmente ocupada).

---

## 6. Resumo das decisões (para citar no vídeo)

| Decisão | Por quê |
|---------|---------|
| Linguagem C + Sockets BSD | Requisito da disciplina; controle fino sobre a rede |
| Servidor thread-por-cliente (pthread) | Atender múltiplos clientes em paralelo (requisito) |
| Protocolo inspirado em HTTP com `LENGTH` | Delimitar o arquivo sobre o fluxo contínuo do TCP |
| `CLOCK_MONOTONIC` para medir tempo | Preciso e imune a ajuste de relógio |
| Topologia CORE por script Python | VM headless; reprodutível e automatizável |
| Validação ping/traceroute/iperf | Confirmar que o gargalo emulado é consistente |
| Arquivos 100 KB e 10 MB | Regimes dominados por latência vs. por banda |
| Concorrência 1/10/50 | Baixa/média/alta escala; evidenciar saturação |
| 4G e Fibra | Tecnologias reais contrastando banda e latência |
| n = 15 repetições | Requisito n > 10; variação converge em ambiente controlado |
