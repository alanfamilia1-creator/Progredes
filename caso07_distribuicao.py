import hashlib
import json
import os
from conexao import conectar, executar

ARQUIVO_LOCAL = "coleta.sh"


def calcular_sha256_local(caminho):
    sha256 = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(4096), b""):
            sha256.update(bloco)
    return sha256.hexdigest()


def main():
    if not os.path.exists(ARQUIVO_LOCAL):
        print(f"Erro: '{ARQUIVO_LOCAL}' não encontrado.")
        return

    hash_local = calcular_sha256_local(ARQUIVO_LOCAL)
    print(f"Hash local: {hash_local}")

    with open("inventario_chave.json", encoding="utf-8") as f:
        inventario = json.load(f)

    for disp in inventario:
        nome = disp["nome"]
        usuario = disp["usuario"]
        # Caminho absoluto explícito (o SFTP não interpreta '~')
        caminho_remoto = f"/home/{usuario}/{ARQUIVO_LOCAL}"

        cliente = None
        sftp = None
        try:
            cliente = conectar(disp)

            # 1. Envia via SFTP e torna executável
            sftp = cliente.open_sftp()
            sftp.put(ARQUIVO_LOCAL, caminho_remoto)
            sftp.chmod(caminho_remoto, 0o755)

            # 2. Calcula o hash remoto
            _, saida_hash, erro_hash = executar(cliente, f"sha256sum {caminho_remoto}")
            partes = saida_hash.strip().split()

            if not partes:
                print(f"[{nome}] FALHA: nao foi possivel calcular o hash remoto ({erro_hash.strip()})")
                continue

            hash_remoto = partes[0]
            print(f"\n[{nome}] Hash remoto: {hash_remoto}")

            # 3. Compara e executa apenas se forem iguais
            if hash_local == hash_remoto:
                print(f"[{nome}] Integridade OK -> Executando {ARQUIVO_LOCAL}:")
                _, saida_exec, _ = executar(cliente, caminho_remoto)
                print(saida_exec.strip())
            else:
                print(f"[{nome}] ALERTA: Hash divergente! Execução cancelada.")

        except Exception as e:
            print(f"[{nome}] ERRO ({type(e).__name__}): {e}")
        finally:
            if sftp:
                sftp.close()
            if cliente:
                cliente.close()


if __name__ == "__main__":
    main()