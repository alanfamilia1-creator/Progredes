# caso06_backup.py
import json
import logging
from datetime import datetime
from pathlib import Path

from conexao import conectar

RETENCAO = 5
REMOTO = "dispositivo.cfg"      # caminho relativo à pasta pessoal do usuário

logging.basicConfig(
    filename="backup.log",
    level=logging.INFO,
    format="%(asctime)s%(levelname)s%(message)s",
)


def fazer_backup(disp):
    pasta = Path("backups") / disp["nome"]
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{datetime.now():%Y-%m-%d_%H%M%S}.cfg"

    cliente = conectar(disp)
    try:
        sftp = cliente.open_sftp()
        try:
            sftp.get(REMOTO, str(destino))
        finally:
            sftp.close()
    finally:
        cliente.close()

    # rotação: mantém somente os mais recentes
    antigos = sorted(pasta.glob("*.cfg"))[:-RETENCAO]
    for arquivo in antigos:
        arquivo.unlink()
    return destino, len(antigos)


with open("inventario_chave.json", encoding="utf-8") as f:
    inventario = json.load(f)

for disp in inventario:
    try:
        destino, removidos = fazer_backup(disp)
        logging.info("%s: backup OK em%s (removidos:%d)", disp["nome"], destino, removidos)
        print(f"{disp['nome']}: OK ->{destino}")
    except Exception as e:
        logging.error("%s: backup FALHOU (%s:%s)", disp["nome"], type(e).__name__, e)
        print(f"{disp['nome']}: FALHA ({type(e).__name__})")