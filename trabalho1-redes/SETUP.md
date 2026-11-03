# SETUP — Ambiente CORE (dentro da VM Vagrant)

Guia passo a passo a partir do momento em que `vagrant ssh` já funcionou
(você está dentro da VM Ubuntu bionic64).

> Todos os comandos abaixo rodam **dentro da VM** (prompt `vagrant@...`).

---

## Passo 1 — Instalar o Docker na VM

```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# valida
sudo docker --version
```

## Passo 2 — Build das imagens do CORE

> Esse passo é demorado (baixa e compila bastante coisa). Tenha paciência.

```bash
git clone https://github.com/coreemu/core.git
cd core
sudo docker build -t emane-python -f dockerfiles/Dockerfile.emane-python .
sudo docker build -t core -f dockerfiles/Dockerfile.ubuntu .
cd ~
```

## Passo 3 — Permitir a GUI (X11) e subir o container

```bash
xhost +local:root 2>/dev/null || true

sudo docker run -itd --name core \
  -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  --privileged --init \
  --entrypoint /opt/core/venv/bin/core-daemon core
```

## Passo 4 — Copiar o projeto pro container e compilar

> Primeiro garanta que a pasta `trabalho1-redes/` está dentro da VM.
> Com Vagrant, a pasta onde você rodou `vagrant up` no Windows aparece em
> `/vagrant` dentro da VM. Se o projeto estiver lá:

```bash
# (opção A) projeto veio via pasta compartilhada /vagrant
sudo docker cp /vagrant/trabalho1-redes core:/root/trabalho1-redes

# (opção B) se você clonou/copiou pro home da VM
# sudo docker cp ~/trabalho1-redes core:/root/trabalho1-redes

# compilar dentro do container
sudo docker exec -it core bash -c "cd /root/trabalho1-redes && make"
```

## Passo 5 — Abrir a GUI do CORE

```bash
sudo docker exec -it core core-gui
```

Na GUI:
1. Abra `core/topologia.imn` (File → Open) **ou** monte manualmente:
   - 2 roteadores no núcleo (R1, R2) ligados entre si
   - uma LAN/switch (rede de acesso) em cada roteador
   - nó **servidor** na rede de acesso de R1; nó **cliente** na de R2
   - Topologia: `cliente -[acesso B]- R2 -[NÚCLEO/gargalo]- R1 -[acesso A]- servidor`
2. Configure o **enlace gargalo** (R1↔R2): botão direito → Configure →
   Bandwidth e Delay (ex.: 4G = 20 Mbps, 50 ms). **NÃO** configure perda (loss).
3. Clique em **Play** (ícone ▶) pra iniciar a emulação.

## Passo 6 — Validar a rede (terminal do nó cliente)

Dê duplo-clique no nó cliente pra abrir um terminal:

```bash
ping -c 5 <IP_DO_SERVIDOR>       # RTT fim-a-fim (deve refletir ~2x o delay do gargalo)
traceroute <IP_DO_SERVIDOR>      # RTT por salto
# vazão: no servidor rode 'iperf -s', no cliente:
iperf -c <IP_DO_SERVIDOR>        # deve bater perto da banda configurada
```

> Os IPs dependem da topologia. No `topologia.imn` fornecido:
> **servidor = 10.0.0.10** e **cliente = 10.0.2.10**.

## Passo 7 — Rodar a aplicação e o experimento

No **nó servidor** (terminal do nó):
```bash
cd /root/trabalho1-redes
./bin/server 8080 serverfiles
```

No **nó cliente** (terminal do nó):
```bash
cd /root/trabalho1-redes
./scripts/gen_files.sh testfiles
./scripts/run_experiment.sh 10.0.0.10 8080 4G 15
```

## Passo 8 — Trocar a tecnologia e repetir

- Reconfigure o enlace gargalo pra **Fibra** (100 Mbps, 5 ms) na GUI.
- Rode novamente:
```bash
./scripts/run_experiment.sh 10.0.0.10 8080 FIBRA 15
```

## Passo 9 — Extrair resultados e analisar

Fora do container (na VM), copie o CSV e gere os gráficos:
```bash
sudo docker cp core:/root/trabalho1-redes/data/resultados.csv ./data/
pip3 install pandas matplotlib numpy scipy   # se ainda não tiver
python3 scripts/analyze.py data/resultados.csv
```

---

## Dicas / solução de problemas

- **`docker` pede sudo toda vez:** normal. Pode adicionar seu usuário ao grupo
  docker (`sudo usermod -aG docker $USER` + relogar) se quiser evitar o `sudo`.
- **GUI não abre (X11):** confirme que rodou `xhost +local:root` e que o
  `-e DISPLAY -v /tmp/.X11-unix...` está no `docker run`. Em VM headless, pode ser
  necessário X server no host.
- **`bind: Address already in use`:** já tem um servidor rodando na porta. Mate o
  processo antigo ou use outra porta.
- **Build do CORE falha por memória:** aumente a RAM da VM (>= 4 GB) no Vagrantfile
  (`vb.memory = 4096`) e `vagrant reload`.
