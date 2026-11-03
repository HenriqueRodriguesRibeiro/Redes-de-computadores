#!/usr/bin/env bash
set -u
SERVER_IP="${1:?informe o IP do servidor}"
PORT="${2:-8080}"
TEC="${3:?informe o rotulo da tecnologia (ex.: 4G ou FIBRA)}"
N="${4:-15}"

CLIENT=./bin/client
CSV="data/resultados.csv"
TESTDIR="testfiles"
mkdir -p data

FILES=("web_100KB.bin" "media_10MB.bin")
CONC=(1 10 50)

echo "=== Experimento | servidor=$SERVER_IP:$PORT | tecnologia=$TEC | n=$N ==="
for f in "${FILES[@]}"; do
  for c in "${CONC[@]}"; do
    for ((rep=1; rep<=N; rep++)); do
      TAG="${TEC};${f};conc=${c};rep=${rep}"
      for ((k=1; k<=c; k++)); do
        $CLIENT "$SERVER_IP" "$PORT" GET "$f" "/tmp/get_${k}.bin" \
          --csv "$CSV" --tag "GET;${TAG};cli=${k}" &
      done
      wait
      for ((k=1; k<=c; k++)); do
        $CLIENT "$SERVER_IP" "$PORT" PUT "$TESTDIR/$f" "put_${k}_${f}" \
          --csv "$CSV" --tag "PUT;${TAG};cli=${k}" &
      done
      wait
    done
    echo "  -> concluido: arquivo=$f concorrencia=$c"
  done
done
echo "=== Fim. Resultados em $CSV ==="
