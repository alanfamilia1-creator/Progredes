import ipaddress
import json
import sys
from conexao import conectar, executar

ARQUIVO_CONF = "~/rede.conf"
ARQUIVO_BACKUP = "~/rede.conf.bak"
NOVO_NTP = "10.0.0.50"


def validar_ip(endereco):
    """Valida se o valor recebido é um endereço IPv4 ou IPv6 válido."""
    try:
        ipaddress.ip_address(endereco)
        return True
    except ValueError:
        return False


def atualizar_ntp_seguro(disp, novo_ntp, simular_falha=False):
    nome = disp["nome"]
    cliente = None
    try:
        cliente = conectar(disp)

        # Garante que o arquivo de configuração inicial existe
        executar(cliente, f"[ -f {ARQUIVO_CONF} ] || echo 'ntp_server=10.0.0.1' > {ARQUIVO_CONF}")

        # (a) Criar cópia de segurança (backup) antes de alterar
        _, _, err_bkp = executar(cliente, f"cp {ARQUIVO_CONF} {ARQUIVO_BACKUP}")
        if err_bkp.strip():
            raise RuntimeError(f"Falha ao criar backup: {err_bkp.strip()}")
        print(f"{nome}: (a) backup criado em {ARQUIVO_BACKUP}")

        # (b) Aplicar a alteração de forma idempotente (remove antigas e insere uma única linha)
        comando_idempotente = (
            f"grep -v '^ntp_server=' {ARQUIVO_CONF} > {ARQUIVO_CONF}.tmp || true; "
            f"echo 'ntp_server={novo_ntp}' >> {ARQUIVO_CONF}.tmp; "
            f"mv {ARQUIVO_CONF}.tmp {ARQUIVO_CONF}"
        )
        executar(cliente, comando_idempotente)
        print(f"{nome}: (b) alteração aplicada (ntp_server={novo_ntp})")

        # (c) Verificar se o valor foi realmente gravado e não duplicou
        valor_esperado = "10.0.0.99" if simular_falha else novo_ntp
        _, saida_verif, _ = executar(cliente, f"grep '^ntp_server=' {ARQUIVO_CONF}")
        linhas = [l.strip() for l in saida_verif.strip().splitlines() if l.strip()]

        if len(linhas) == 1 and linhas[0] == f"ntp_server={valor_esperado}":
            print(f"{nome}: (c) verificação OK -> '{linhas[0]}'")
        else:
            # (d) Reverter automaticamente em caso de falha na verificação
            print(f"{nome}: [ALERTA] verificação falhou! Encontrado: {linhas}")
            executar(cliente, f"mv {ARQUIVO_BACKUP} {ARQUIVO_CONF}")
            print(f"{nome}: (d) reversão (rollback) concluída a partir do backup")

    except Exception as e:
        print(f"{nome}: FALHA ({type(e).__name__}:{e})")
    finally:
        if cliente:
            cliente.close()


def main():
    if not validar_ip(NOVO_NTP):
        print(f"ERRO: IP inválido '{NOVO_NTP}'. Abortando.")
        sys.exit(1)

    # Lê o inventário configurado com a chave pública Ed25519
    with open("inventario_chave.json", encoding="utf-8") as f:
        inventario = json.load(f)

    print("=== 1. APLICAÇÃO INICIAL ===")
    for disp in inventario:
        atualizar_ntp_seguro(disp, NOVO_NTP)

    print("\n=== 2. TESTE DE IDEMPOTÊNCIA (SEGUNDA EXECUÇÃO) ===")
    for disp in inventario:
        atualizar_ntp_seguro(disp, NOVO_NTP)

    print("\n=== 3. TESTE DE REVERSÃO AUTOMÁTICA (ROLLBACK) ===")
    atualizar_ntp_seguro(inventario[0], NOVO_NTP, simular_falha=True)


if __name__ == "__main__":
    main()