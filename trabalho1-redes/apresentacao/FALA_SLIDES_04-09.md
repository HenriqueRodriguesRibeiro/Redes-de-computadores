# Minha fala — Slides 04 a 09

**Responsável:** [seu nome] · Parte técnica (como funciona + resultados)
**Tempo-alvo do bloco:** ~3:30 a 4:00 min

> Dica geral: **não leia o slide** — ele é o apoio visual. Fale olhando pra
> câmera/tela, com suas palavras. Os trechos em **negrito** são onde vale dar
> ênfase. Pausas curtas entre os slides ajudam.

---

## 🎙️ Slide 4 — Como: protocolo e concorrência · ~0:45

> "Agora vou explicar **como** a aplicação funciona por dentro.
>
> O protocolo que criamos é **inspirado no HTTP**: cada requisição tem um
> cabeçalho de texto com um campo chamado `LENGTH`, que informa o tamanho do
> arquivo em bytes. Esse campo é **essencial**, e aqui está o porquê: o TCP
> entrega os dados como um **fluxo contínuo de bytes**, sem marcar onde termina
> uma mensagem e começa a outra. Então, sem o `LENGTH`, o receptor não saberia
> quando parar de ler. Com ele, sabe exatamente quantos bytes esperar para
> remontar o arquivo.
>
> Sobre a concorrência: o servidor segue o modelo **uma thread por cliente**. A
> cada nova conexão aceita, ele cria uma thread dedicada com `pthread`. Isso
> permite atender **vários clientes ao mesmo tempo** — e é justamente isso que
> queremos estressar no experimento: a **disputa pela banda** quando muitos
> clientes competem.
>
> Além disso, cuidamos da robustez: envio e recepção em laço para garantir que
> todos os bytes trafeguem, tratamento de desconexões e medição de tempo com um
> relógio monotônico, que é mais preciso."

**Ênfase:** o *porquê* do `LENGTH` (TCP é fluxo de bytes) e o *porquê* das threads
(expor a disputa pela banda). São os dois pontos que mostram domínio técnico.

---

## 🎙️ Slide 5 — Como: topologia emulada no CORE · ~0:40

> "Este é o ambiente de testes, montado no emulador CORE. A topologia segue o
> que o enunciado pede: temos duas **redes de acesso** e um **núcleo**. O
> servidor fica em uma ponta, o cliente na outra, e o **enlace central, entre os
> roteadores R1 e R2, é o nosso gargalo** — é nele que configuramos a largura de
> banda e a latência de cada tecnologia.
>
> Uma decisão nossa: montamos essa topologia por **script em Python**, usando a
> API do CORE, em vez da interface gráfica — porque a máquina virtual era
> *headless*, sem ambiente gráfico. Isso trouxe uma vantagem: o experimento
> ficou totalmente **reprodutível e automatizado**.
>
> E antes de medir qualquer coisa, **validamos** que o ambiente estava
> consistente: o **ping** confirmou que o tempo de ida e volta corresponde a
> cerca de duas vezes o atraso configurado no gargalo; o **traceroute** mostrou
> que a latência se concentra exatamente no salto do núcleo; e o **iperf**
> confirmou que a vazão bate com a banda que configuramos."

**Ênfase:** "o enlace central é o gargalo" (aponte com o cursor) e a validação
(ping/traceroute/iperf) — é um requisito explícito do enunciado.

---

## 🎙️ Slide 6 — Por que: fatores experimentais · ~0:40

> "Para avaliar o desempenho, cruzamos **quatro fatores**.
>
> Primeiro, o **tamanho do arquivo**: escolhemos 100 KB, que representa uma
> página web típica, e 10 MB, que representa uma foto ou vídeo curto. Segundo, a
> **operação**: GET, de download, e PUT, de upload. Terceiro, a **concorrência**:
> 1, 10 e 50 clientes simultâneos — cenários de baixa, média e alta escala. E
> quarto, a **tecnologia de rede** no gargalo: 4G e Fibra, duas tecnologias
> reais de acesso.
>
> Combinando tudo, são **24 configurações diferentes**. Repetimos cada uma **15
> vezes** — o enunciado pede mais de 10 repetições. Como a telemetria é coletada
> por cliente, isso resultou em **mais de 7 mil operações medidas** no total."

**Ênfase:** os pares de contraste — "100 KB vs 10 MB", "baixa vs alta escala",
"4G vs Fibra". E o número final: **7 mil operações**.

---

## 🎙️ Slide 7 — A chave para interpretar tudo · ~0:35

> "Antes de mostrar os resultados, quero deixar **uma ideia que explica todos os
> gráficos** a seguir.
>
> Para o **arquivo pequeno, de 100 KB**, quem domina o desempenho é a
> **latência**. A transferência é tão rápida que o tempo é gasto, na maior
> parte, no ida e volta da rede — a largura de banda quase não influencia.
>
> Já para o **arquivo grande, de 10 MB**, quem domina é a **banda**. A
> transferência é longa o suficiente para que o tempo seja basicamente o
> tamanho do arquivo dividido pela banda disponível. Aqui a latência pesa pouco,
> e é esse caso que **satura** quando há muitos clientes.
>
> Guardem essa ideia: **arquivo pequeno, latência; arquivo grande, banda**."

**Ênfase:** repita o resumo no final — é o fio condutor de toda a discussão. Fale
devagar nas palavras "LATÊNCIA" e "BANDA" (que estão grandes no slide).

---

## 🎙️ Slide 8 — Resultado: saturação · ~0:45

> "Vamos aos resultados, começando pelo arquivo de 10 MB no GET, nesta tabela.
>
> Olhem a coluna do tempo no **4G**: com **1 cliente**, a transferência leva
> cerca de **5 segundos**. Com **10 clientes**, sobe para 42 segundos. E com
> **50 clientes**, chega a **214 segundos** — ou seja, cerca de **42 vezes mais
> lenta** do que com um único cliente.
>
> O motivo está na última coluna, a vazão: a banda do gargalo é um recurso
> **compartilhado**. Quanto mais clientes competem, menos banda sobra para cada
> um — por isso a vazão por cliente despenca de quase 17 para menos de meio
> megabit por segundo.
>
> A Fibra segue o mesmo padrão, mas sempre com tempos bem menores, porque tem
> cinco vezes mais banda."

**Ênfase:** a progressão **5s → 42s → 214s** (aponte cada linha). O "42 vezes
mais lenta" é o número de impacto.

---

## 🎙️ Slide 9 — A prova: vazão agregada ≈ banda do gargalo · ~0:45

> "E aqui está, para mim, o resultado **mais importante** do trabalho: a prova de
> que o experimento é consistente com a física da rede.
>
> Se pegarmos a vazão **por cliente** e multiplicarmos pelo **número de
> clientes**, obtemos a vazão **agregada** — o total que passou pelo gargalo. No
> **4G**, com 10 clientes, dá **10 vezes 2, igual a 20 megabits por segundo** —
> que é **exatamente** a banda que configuramos no gargalo. Com 50 clientes, dá
> 19,6 — praticamente o mesmo teto.
>
> Na **Fibra**, com 50 clientes, a conta dá cerca de **90 megabits por segundo**,
> aproximando-se dos 100 que configuramos — a pequena diferença é o overhead
> natural do TCP.
>
> Ou seja: o sistema **satura no teto da banda**. Isso identifica claramente o
> **gargalo** e o **ponto de saturação**, e **valida** tanto a nossa
> implementação quanto o ambiente emulado — os números batem com o esperado."

**Ênfase:** a conta "**10 × 2 = 20, exatamente a banda configurada**" é o ápice.
Diga com convicção — é o que mais impressiona. Feche com "satura no teto da banda".

---

## Transição para o próximo colega

> "Agora o [nome do colega] vai mostrar os gráficos que detalham esse
> comportamento." (ou o que fizer sentido na divisão de vocês)

---

## Resumo de tempo deste bloco

| Slide | Tema | Tempo |
|-------|------|-------|
| 4 | Protocolo + concorrência | 0:45 |
| 5 | Topologia + validação | 0:40 |
| 6 | Fatores experimentais | 0:40 |
| 7 | Conceito latência vs banda | 0:35 |
| 8 | Saturação (tabela) | 0:45 |
| 9 | A prova (contas) | 0:45 |
| | **Total** | **~3:50** |

## 3 dicas rápidas
1. **Ensaie o slide 9** mais que os outros — a conta precisa sair natural.
2. Nos slides 8 e 9, **aponte os números com o cursor** enquanto fala.
3. Se estiver acelerado, o slide 4 é o que pode encurtar (corte a parte da
   robustez). Se estiver sobrando tempo, detalhe mais o `LENGTH`.
