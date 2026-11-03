#!/usr/bin/env bash
set -e
DEST="${1:-testfiles}"
mkdir -p "$DEST"
dd if=/dev/urandom of="$DEST/web_100KB.bin"  bs=1024 count=100   status=none
dd if=/dev/urandom of="$DEST/media_10MB.bin" bs=1024 count=10240 status=none
echo "Arquivos gerados em '$DEST':"
ls -lh "$DEST"
