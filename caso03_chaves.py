# caso03_chaves.py
import json
import os

from conexao import conectar, executar

os.environ.pop("SSH_SENHA", None)   # garante que nenhuma senha esteja disponível

with open("inventario_chave.json", encoding="utf-8") as f:
    inventario = json.load(f)

for disp in inventario:
    try:
        cliente = conectar(disp)
        _, saida, _ = executar(cliente, "whoami")
        print(f"{disp['nome']}: autenticado por chave como '{saida}'")
        cliente.close()
    except Exception as e:
        print(f"{disp['nome']}: FALHA ({type(e).__name__}:{e})")

# Teste negativo: chave inexistente
invalido = dict(inventario[0], chave="/tmp/chave_que_nao_existe")
try:
    conectar(invalido)
except Exception as e:
    print(f"Teste negativo ->{type(e).__name__}:{e}")