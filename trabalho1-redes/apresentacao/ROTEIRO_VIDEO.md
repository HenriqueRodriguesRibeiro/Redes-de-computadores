# Roteiro do Vídeo-Relatório (até 10 min)

**Trabalho 1 — Redes de Computadores | ICT/UNIFESP**

Roteiro cronometrado casando **slide × tempo × fala**. Alvo: **~9 min**
(folga para os 10 min). Os textos em _itálico_ são sugestões de fala — adapte
para o seu jeito, não decore palavra por palavra.

> 📊 Abra `slides.html` em tela cheia (tecla **F**) e grave a tela + narração.
> Nos slides de gráfico, aponte com o cursor o que estiver descrevendo.

---

## Distribuição do tempo (visão geral)

| Bloco | Slides | Tempo | Acumulado |
|-------|--------|-------|-----------|
| 1. Abertura/motivação | 1–2 | 1:00 | 1:00 |
| 2. O que / Como | 3–5 | 2:00 | 3:00 |
| 3. Por que (fatores) + conceito | 6–7 | 1:15 | 4:15 |
| 4. Resultados (tabela + prova) | 8–9 | 1:30 | 5:45 |
| 5. Gráficos (discussão) | 10–13 | 2:15 | 8:00 |
| 6. Comparação + conclusões | 14–15 | 0:50 | 8:50 |
| 7. Contribuições/autoavaliação | 16–17 | 0:40 | 9:30 |

---

## Bloco 1 — Abertura e motivação · ~1:00

### Slide 1 (capa) · 0:15
> _"Olá, somos o grupo formado por Henrique, Lucas e Pedro Henrique. Este é o
> Trabalho 1 de Redes de Computadores:
> avaliação de desempenho de uma aplicação cliente-servidor de arquivos,
> implementada em C e testada numa rede emulada no CORE."_

### Slide 2 (introdução/motivação) · 0:45
> _"Transferir arquivos é uma das operações mais comuns da Internet. A pergunta
> que investigamos foi: como o tamanho do arquivo, o número de clientes
> simultâneos e a tecnologia de rede afetam o tempo de resposta e a vazão?
> Para responder de forma controlada, implementamos a aplicação e a medimos
> numa topologia emulada, variando esses fatores."_

---

## Bloco 2 — O que e como · ~2:00

### Slide 3 (o que foi desenvolvido) · 0:35
> _"Desenvolvemos uma aplicação em C com duas operações: GET, para baixar um
> arquivo do servidor, e PUT, para enviar. O servidor é concorrente — uma
> thread por cliente — e responde com códigos de status no estilo HTTP. Além
> disso, montamos o ambiente de experimento e scripts de automação e análise."_

### Slide 4 (protocolo e concorrência) · 0:45
> _"O protocolo é inspirado no HTTP, com um cabeçalho textual e o campo LENGTH.
> Esse campo é essencial porque o TCP é um fluxo contínuo de bytes, sem
> fronteiras de mensagem — então o receptor precisa saber exatamente quantos
> bytes ler para delimitar o arquivo. O servidor usa o modelo thread-por-cliente:
> a cada conexão, cria uma thread. Isso atende vários clientes em paralelo e
> expõe justamente o que queremos medir: a disputa pela banda do gargalo."_

### Slide 5 (topologia CORE) · 0:40
> _"A topologia tem duas redes de acesso e um núcleo. O servidor fica numa
> ponta, o cliente na outra, e o enlace central é o gargalo, onde configuramos
> banda e latência. Montamos tudo por script Python, sem interface gráfica.
> Antes dos experimentos, validamos a consistência com ping, traceroute e
> iperf — confirmando que o RTT e a vazão batem com o que configuramos."_

---

## Bloco 3 — Por que e o conceito-chave · ~1:15

### Slide 6 (fatores experimentais) · 0:40
> _"Cruzamos quatro fatores: dois tamanhos de arquivo, 100 KB e 10 MB; as
> operações GET e PUT; três níveis de concorrência — 1, 10 e 50 clientes; e
> duas tecnologias de rede, 4G e Fibra. Isso dá 24 configurações, cada uma
> repetida 15 vezes — mais de 7 mil execuções no total."_

### Slide 7 (conceito: latência vs banda) · 0:35
> _"Antes dos resultados, a chave para entender tudo: o arquivo pequeno é
> dominado pela LATÊNCIA — a transferência é tão curta que o que pesa é o
> tempo de ida e volta. Já o arquivo grande é dominado pela BANDA — o tempo é
> basicamente o tamanho dividido pela largura de banda. Guardem essa ideia."_

---

## Bloco 4 — Resultados: a prova numérica · ~1:30

### Slide 8 (tabela de saturação) · 0:45
> _"Olhando o arquivo de 10 MB: com 1 cliente, a transferência leva cerca de 5
> segundos no 4G. Com 50 clientes simultâneos, salta para 214 segundos — cerca
> de 42 vezes mais lenta. Isso acontece porque a banda do gargalo é um recurso
> compartilhado: quanto mais clientes, menos banda para cada um."_

### Slide 9 (a prova) · 0:45
> _"E aqui está a prova de que o experimento é consistente: se multiplicarmos a
> vazão por cliente pelo número de clientes, obtemos a vazão agregada. No 4G,
> dá 20 Mbps — exatamente a banda que configuramos no gargalo. Na Fibra,
> aproxima-se dos 100 Mbps. Ou seja, o sistema satura no teto da banda — isso
> valida tanto a implementação quanto o ambiente emulado."_

---

## Bloco 5 — Gráficos (a discussão principal) · ~2:15

> 💡 Aqui aponte os elementos nos gráficos com o cursor. Os dois primeiros slides
> mostram **10 MB e 100 KB lado a lado** — use o contraste para explicar
> "banda vs latência".

### Slide 10 (TEMPO: 10 MB vs 100 KB) · 0:40
> _"Aqui comparamos o tempo de resposta nos dois tamanhos. No arquivo de 10 MB,
> à esquerda, as curvas do 4G disparam com a concorrência, até 214 segundos — é
> a banda saturando. Já no de 100 KB, à direita, os tempos são muito baixos e
> pouco sensíveis à concorrência: aqui quem manda é a latência, por isso a Fibra
> fica bem abaixo do 4G."_

### Slide 11 (VAZÃO em Mbps: 10 MB vs 100 KB) · 0:45
> _"A vazão, agora em Mbps. No 10 MB, a vazão por cliente despenca e a soma
> satura no teto da banda do gargalo. No 100 KB, a Fibra chega a mais de 100
> Mbps com um cliente — mostrando que, para arquivos pequenos, a banda nem é o
> limite; o que pesa é a latência. É o gráfico que identifica o ponto de
> saturação."_

### Slide 12 (CDF) · 0:30
> _"A CDF mostra a distribuição acumulada dos tempos. As curvas da Fibra ficam
> à esquerda — transferências rápidas; o 4G tem uma cauda longa até 214
> segundos. Com ela conseguimos ler percentis, como o p95, útil para garantias
> de qualidade de serviço."_

### Slide 13 (variabilidade) · 0:20
> _"E a variabilidade: sob alta concorrência a dispersão aumenta, porque o
> escalonamento faz alguns clientes terminarem antes de outros."_

---

## Bloco 6 — Comparação e conclusões · ~0:50

### Slide 14 (Fibra vs 4G) · 0:20
> _"Resumindo a comparação: no arquivo pequeno, a vantagem da Fibra vem da
> latência; no grande, vem da banda. Cada fator pesa num regime diferente."_

### Slide 15 (conclusões) · 0:30
> _"Concluindo: a banda do gargalo limita os arquivos grandes sob concorrência,
> e o sistema satura no teto configurado. A latência domina os arquivos
> pequenos. O modelo thread-por-cliente cumpriu o requisito de concorrência. E
> os resultados são fisicamente coerentes — vazão agregada igual à banda, RTT
> igual ao dobro do atraso — o que valida todo o trabalho."_

---

## Bloco 7 — Contribuições e autoavaliação · ~0:40

### Slide 16 (contribuições) · 0:25
> _"Sobre as contribuições, embora as decisões tenham sido tomadas em grupo,
> cada um teve um foco: o Pedro Henrique cuidou do protocolo e da implementação
> do servidor em C; o Lucas, do cliente com telemetria e da análise estatística
> com os gráficos; e o Henrique, da montagem do ambiente CORE e da execução dos
> experimentos de ponta a ponta, além da documentação."_

### Slide 17 (autoavaliação) · 0:15
> _"Na autoavaliação, consideramos que atendemos a todos os requisitos, com
> resultados coerentes. O maior desafio foi o ambiente headless, resolvido com
> automação; e o principal aprendizado foi ver, na prática, latência e banda
> dominando regimes diferentes, além da saturação sob concorrência. Obrigado!"_

---

## Dicas de gravação

- **Ensaiar 1–2 vezes** cronometrando: se passar de 10 min, corte detalhes dos
  slides 4 e 5 (os mais densos).
- **Dividir a narração** entre os integrantes (o requisito pede a contribuição
  de cada um — falar no vídeo já evidencia isso).
- **Compartilhar a tela** com os slides em tela cheia; nos gráficos, mover o
  cursor para guiar o olhar.
- **Não ler o slide** — o slide é apoio; fale com suas palavras.
- Deixe o slide 1 e o 16 com os **nomes e as contribuições preenchidos** antes
  de gravar.
- Áudio limpo importa mais que vídeo perfeito — grave num ambiente silencioso.

## Checklist final antes de enviar

- [ ] Slides 1 e 16 preenchidos (nomes, contribuições, autoavaliação)
- [ ] Vídeo com até 10 min
- [ ] Vídeo subido na nuvem (Drive/YouTube não listado) e **link** testado
- [ ] Entregar no classroom: **código do servidor** + **link do vídeo**
      (NÃO enviar o arquivo de vídeo)
