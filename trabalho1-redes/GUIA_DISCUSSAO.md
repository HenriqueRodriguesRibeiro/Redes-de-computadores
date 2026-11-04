# Guia de Discussão dos Resultados

**UC Redes de Computadores — ICT/UNIFESP | Trabalho 1**

Este guia ajuda a **interpretar os gráficos** e estruturar a parte "Discussão dos
resultados obtidos" do vídeo-relatório. Para cada gráfico, explicamos **o que
olhar**, **o que é esperado teoricamente** e **como explicar o fenômeno**.

> ⚠️ Os valores numéricos citados abaixo são **referências/previsões**. Substitua
> pelos números reais do seu `data/resumo.csv` depois de rodar o `analyze.py`.
> Já temos os dados da FIBRA; o 4G confirma o contraste.

---

## 0. Os dois conceitos-chave que explicam TUDO

Antes dos gráficos, fixe estas duas ideias — elas explicam quase todos os
resultados:

1. **Arquivo pequeno (100 KB) → dominado pela LATÊNCIA.**
   A transferência é tão curta que o tempo é gasto principalmente no
   *ida-e-volta* (RTT), no estabelecimento da conexão e no *slow start* do TCP.
   A banda disponível quase não importa.

2. **Arquivo grande (10 MB) → dominado pela BANDA (largura de banda).**
   A transferência é longa o suficiente para o TCP atingir regime permanente;
   o tempo passa a ser basicamente `tamanho ÷ banda`. A latência pesa pouco.

Com isso em mente, cada gráfico vira uma confirmação dessas duas forças.

---

## 1. Tempo de resposta × concorrência (gráfico de barras/linhas com IC 95%)
**Arquivos:** `data/tempo_web_100KB.bin.png` e `data/tempo_media_10MB.bin.png`

### O que olhar
Eixo X = nº de clientes concorrentes (1, 10, 50); eixo Y = tempo médio (s), com
barras de erro (intervalo de confiança 95%). Uma curva por tecnologia-operação.

### O que é esperado
- **Com 1 cliente:** tempo baixo (linha de base, sem disputa).
- **Conforme a concorrência cresce (10 → 50):** o tempo médio **aumenta**, porque
  os clientes **disputam a mesma banda** do gargalo. Com 50 clientes, cada um
  recebe ~1/50 da banda → cada transferência demora muito mais.
- **Fibra sempre abaixo do 4G** (mais banda + menos latência).

### Como explicar
> "O tempo de resposta cresce com a concorrência porque a banda do gargalo é um
> recurso compartilhado. Com N clientes simultâneos, a banda efetiva por cliente
> cai para ~banda/N, então cada transferência demora proporcionalmente mais.
> Isso é mais evidente no arquivo de 10 MB (dominado por banda) do que no de
> 100 KB (dominado por latência)."

### Dado real da Fibra (já coletado — confira no seu CSV)
- `media_10MB`, Fibra, conc=50: tempo ~**51-52 s** por cliente (vazão caiu p/ ~1.6 Mbps).
- `media_10MB`, Fibra, conc=1: muito mais rápido (banda quase toda para 1 cliente).
- → A diferença entre conc=1 e conc=50 **é a prova visual da saturação**.

---

## 2. Boxplot do tempo de resposta
**Arquivo:** `data/boxplot_tempo.png`

### O que olhar
Cada caixa = distribuição dos tempos de uma combinação tecnologia-operação.
A caixa mostra mediana (linha central), quartis (bordas) e *outliers* (pontos).

### O que é esperado
- **Caixas do 4G mais altas e mais largas** que as da Fibra (tempos maiores e
  mais variáveis).
- **Maior dispersão (caixa alta + outliers)** nos cenários de alta concorrência:
  sob disputa, alguns clientes terminam antes e outros depois, aumentando a
  variância.

### Como explicar
> "O boxplot revela não só o tempo típico (mediana), mas a **variabilidade**.
> Sob alta concorrência, a dispersão aumenta: o escalonamento do TCP e do
> sistema faz alguns clientes serem servidos mais rápido que outros. A Fibra
> apresenta distribuição mais concentrada (previsível); o 4G, mais espalhada."

---

## 3. CDF do tempo de resposta
**Arquivo:** `data/cdf_tempo.png`

### O que olhar
Curva acumulada: eixo X = tempo (s); eixo Y = P(tempo ≤ x), de 0 a 1.
Uma curva por tecnologia-operação.

### O que é esperado
- **Curva da Fibra "sobe" mais à esquerda** (tempos menores): a maioria das
  transferências termina rápido.
- **Curva do 4G deslocada à direita** (tempos maiores).
- Curvas mais "verticais" = desempenho consistente; mais "deitadas" = maior
  variação.

### Como explicar (é o gráfico que mais impressiona)
> "A CDF permite ler **percentis** diretamente. Por exemplo, olhando onde a
> curva cruza Y=0,95, temos o **p95**: o tempo abaixo do qual 95% das
> transferências se completam — uma métrica muito usada em SLA/QoS. Vemos que o
> p95 da Fibra é bem menor que o do 4G, confirmando a superioridade da fibra em
> previsibilidade e rapidez."

---

## 4. Vazão × concorrência (o gráfico da SATURAÇÃO)
**Arquivo:** `data/vazao_concorrencia.png`

### O que olhar
Eixo X = concorrência; eixo Y = vazão média **por cliente** (Mbps).

### O que é esperado — ESTE É O PONTO CENTRAL DO TRABALHO
- Com **1 cliente**, a vazão por cliente é **alta** (quase toda a banda do
  gargalo disponível para ele).
- Conforme a concorrência cresce, a vazão **por cliente despenca**, porque a
  banda total (fixa) é dividida entre mais clientes.
- **A vazão agregada (soma de todos)** tende a saturar perto da **banda do
  gargalo** — é o **ponto de saturação**: a partir dali, adicionar clientes não
  aumenta o total, só reparte mais fino.

### Como explicar (identificando o gargalo e a saturação — requisito 2.4)
> "Este gráfico identifica o **gargalo** e o **ponto de saturação**. A vazão por
> cliente cai com a concorrência porque a banda do enlace gargalo é finita e
> compartilhada. Somando a vazão de todos os clientes, ela se aproxima do teto
> da banda configurada (20 Mbps no 4G, 100 Mbps na Fibra) — esse teto é o
> **gargalo**. O **ponto de saturação** é a concorrência a partir da qual o
> enlace já está 100% ocupado e o sistema não entrega mais throughput agregado."

### Conta de verificação (cite no vídeo — dá credibilidade)
- Fibra, `media_10MB`, conc=50: vazão/cliente ~1.6 Mbps.
  **50 × 1.6 ≈ 80 Mbps agregados** → coerente com os ~100 Mbps do gargalo
  (menos o overhead de TCP e a latência). ✅
- Faça a mesma conta com o 4G (deve se aproximar de ~20 Mbps agregados).

---

## 5. Comparações que valem destacar no vídeo

### 5.1 Fibra vs 4G
- Fibra: menor tempo e maior vazão em **todos** os cenários.
- No **arquivo pequeno (100 KB)**, a vantagem da Fibra vem mais da **latência**
  (5 ms vs 50 ms): menos RTT para estabelecer e completar.
- No **arquivo grande (10 MB)**, a vantagem vem mais da **banda** (100 vs 20 Mbps).

### 5.2 Arquivo pequeno vs grande
- 100 KB: tempos baixos, pouco sensíveis à concorrência (latência domina).
- 10 MB: tempos altos, **muito** sensíveis à concorrência (banda domina e satura).

### 5.3 GET vs PUT
- Geralmente simétricos em ordem de grandeza (mesmo volume de dados).
- Pequenas diferenças podem surgir do padrão de I/O (leitura vs escrita em disco
  no servidor) e do sentido do tráfego. Comente se observar diferença
  consistente nos dados.

---

## 6. Roteiro sugerido para a fala (discussão, ~3-4 min do vídeo)

1. **Abrir com o conceito:** "latência domina arquivo pequeno, banda domina
   arquivo grande" (seção 0).
2. **Mostrar tempo × concorrência:** o tempo sobe com mais clientes → disputa
   pela banda.
3. **Mostrar vazão × concorrência:** vazão/cliente cai, agregada satura no teto
   do gargalo → **identificar gargalo e saturação** (requisito).
4. **Mostrar CDF:** ler o p95, comparar Fibra vs 4G (previsibilidade).
5. **Fechar com a comparação Fibra vs 4G** e a conta de verificação
   (50 × vazão ≈ banda do gargalo) para mostrar coerência física.

---

## 7. Conclusões que os dados sustentam

- A **banda do enlace gargalo** é o fator limitante para arquivos grandes sob
  concorrência — o sistema **satura** no teto da banda configurada.
- A **latência** domina o desempenho de arquivos pequenos; por isso a Fibra
  (5 ms) se destaca mesmo onde a banda não é o gargalo.
- O **modelo thread-por-cliente** cumpre o requisito de concorrência e deixa o
  gargalo de rede (não a CPU do servidor) ser o fator dominante — o que é
  justamente o que queríamos medir.
- Os resultados são **fisicamente coerentes**: vazão agregada ≈ banda do
  gargalo; RTT do ping ≈ 2× o atraso configurado. Isso valida tanto a
  implementação quanto o ambiente emulado.
