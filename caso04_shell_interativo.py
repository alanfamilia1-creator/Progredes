import json
import time
from conexao import conectar, executar


def ler_buffer(shell, espera=0.5):
    time.sleep(espera)
    saida = ""
    while shell.recv_ready():
        saida += shell.recv(4096).decode("utf-8", errors="ignore")
    return saida


with open("inventario_chave.json", encoding="utf-8") as f:
    inventario = json.load(f)

dispositivo = inventario[0]  # R1

# 1. Sessão interativa com invoke_shell (mantém o estado)
print("=== 1. SESSÃO INTERATIVA (invoke_shell) ===")
cliente = conectar(dispositivo)
shell = cliente.invoke_shell()
ler_buffer(shell, espera=0.5)  # Limpa o banner inicial

comandos = [
    "cd /tmp",
    "pwd",
    "export AMBIENTE=PRODUCAO",
    "echo $AMBIENTE"
]

for cmd in comandos:
    shell.send(cmd + "\n")
    resposta = ler_buffer(shell, espera=0.4)
    print(f"[Enviado]: {cmd}")
    print(f"[Saída]  :\n{resposta.strip()}\n" + "-" * 40)

shell.close()
cliente.close()

# 2. Comandos avulsos com exec_command (sem estado)
print("\n=== 2. COMANDOS AVULSOS (exec_command) ===")
cliente = conectar(dispositivo)

for cmd in comandos:
    _, saida, erro = executar(cliente, cmd)
    print(f"[Enviado]: {cmd}")
    print(f"[Saída]  : '{saida.strip()}' (Erro: '{erro.strip()}')")

cliente.close()