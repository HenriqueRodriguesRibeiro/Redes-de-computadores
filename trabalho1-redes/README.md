# Trabalho 1 - Redes de Computadores

**Avaliação de Desempenho de Cliente-Servidor de Arquivos** — ICT/UNIFESP

Aplicação cliente-servidor de arquivos em C com sockets, servidor concorrente
(uma thread por cliente via `pthread`), suportando `GET` e `PUT` com códigos de
erro inspirados em HTTP. Em seguida, avaliação de desempenho em topologia emulada
no CORE, variando tamanho de arquivo, concorrência e tecnologia de rede no gargalo.

## Estrutura

```
trabalho1-redes/
  src/
    protocol.h          # protocolo + códigos de status/erro
    common.h            # assinaturas das funções utilitárias
    common.c            # send/recv robustos, parsing
    server.c            # servidor concorrente (pthread) GET/PUT
    client.c            # cliente CLI + telemetria (CSV)
  Makefile
  scripts/
    gen_files.sh        # gera arquivos de teste (100 KB e 10 MB)
    run_experiment.sh   # automação dos experimentos (n repetições)
    analyze.py          # estatísticas + gráficos
  core/
    topologia.imn       # topologia CORE
  data/                 # CSVs coletados + gráficos
  README.md
```

## 1. Compilar

```bash
make
# gera bin/server e bin/client
```

## 2. Testar localmente (sanidade)

```bash
# terminal 1 - servidor (porta 8080, diretório base serverfiles/)
./bin/server 8080 serverfiles

# terminal 2 - cliente
echo "ola mundo" > teste.txt
./bin/client 127.0.0.1 8080 PUT teste.txt arquivo.txt   # 201 CREATED
./bin/client 127.0.0.1 8080 GET arquivo.txt saida.txt   # 200 OK
./bin/client 127.0.0.1 8080 GET nao_existe.txt out.txt  # 404 NOT FOUND
```

## 3. Protocolo (inspirado em HTTP)

**GET:**
```
GET <caminho>\r\n
\r\n
```
Resposta (sucesso):
```
<codigo> <mensagem>\r\n
LENGTH: <tamanho_em_bytes>\r\n
\r\n
<bytes do arquivo...>
```

**PUT:**
```
PUT <caminho>\r\n
LENGTH: <tamanho_em_bytes>\r\n
\r\n
<bytes do arquivo...>
```
Resposta:
```
<codigo> <mensagem>\r\n
\r\n
```

**Códigos de status:** 200 OK, 201 CREATED, 400 BAD REQUEST,
403 FORBIDDEN, 404 NOT FOUND, 500 INTERNAL ERROR.

## 4. Experimento no CORE

Ver seção 3 do documento de planejamento. Resumo:

```bash
# No nó servidor:
cd /root/trabalho1-redes
./bin/server 8080 serverfiles

# No nó cliente (validar rede primeiro):
ping -c 5 <IP_SERVIDOR>
traceroute <IP_SERVIDOR>
iperf -c <IP_SERVIDOR>        # rode 'iperf -s' no servidor antes

# Rodar experimento:
./scripts/gen_files.sh testfiles
./scripts/run_experiment.sh <IP_SERVIDOR> 8080 4G 15
# reconfigurar o gargalo para Fibra e repetir:
./scripts/run_experiment.sh <IP_SERVIDOR> 8080 FIBRA 15
```

## 5. Análise

```bash
python3 scripts/analyze.py data/resultados.csv
# gera data/resumo.csv e os gráficos PNG
```

## Plano experimental

| Fator        | Valores                                      |
|--------------|----------------------------------------------|
| Arquivo      | ~100 KB (página web), ~10 MB (foto/vídeo)    |
| Operação     | GET, PUT                                      |
| Concorrência | 1, 10, 50 clientes                            |
| Rede/gargalo | 4G/LTE (~20 Mbps/50 ms), Fibra (~100 Mbps/5 ms) |
| Repetições   | n = 15                                        |

Total: 2 × 2 × 3 × 2 = 24 configurações × 15 = 360 execuções.
