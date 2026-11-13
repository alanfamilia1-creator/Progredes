from datetime import datetime
import difflib
import json
from conexao import conectar, executar

ARQUIVO_REF = "referencia.cfg"
RELATORIO_SAIDA = "relatorio_conformidade.txt"


def preparar_cenario_laboratorio(inventario):
    """Garante que os dispositivos tenham dispositivo.cfg e provoca divergência no R2."""
    with open(ARQUIVO_REF, encoding="utf-8") as f:
        conteudo_ref = f.read().strip()

    for disp in inventario:
        nome = disp["nome"]
        cliente = conectar(disp)
        try:
            # R2 recebe alteração manual no snmp_community para simular configuration drift
            if nome == "R2":
                cfg_remota = conteudo_ref.replace(
                    "snmp_community=corp_ro_99",
                    "snmp_community=public"
                )
            else:
                cfg_remota = conteudo_ref

            texto_completo = f"hostname={nome}\n{cfg_remota}\n"
            executar(cliente, f"cat << 'EOF' > ~/dispositivo.cfg\n{texto_completo}EOF")
        finally:
            cliente.close()


def auditar_dispositivo(disp, linhas_ref):
    nome = disp["nome"]
    usuario = disp["usuario"]
    caminho_remoto = f"/home/{usuario}/dispositivo.cfg"

    cliente = None
    sftp = None
    try:
        cliente = conectar(disp)
        sftp = cliente.open_sftp()

        # Lê o arquivo remoto diretamente em memória sem gravá-lo no disco local
        with sftp.open(caminho_remoto, "r") as arquivo_remoto:
            conteudo_remoto = arquivo_remoto.read().decode("utf-8", errors="ignore")

        # Filtra a linha 'hostname=' (que é única por equipamento) para comparar apenas o padrão
        linhas_remotas_filtradas = [
            linha.strip()
            for linha in conteudo_remoto.splitlines()
            if linha.strip() and not linha.strip().startswith("hostname=")
        ]

        # Gera diff unificado entre a referência e o equipamento
        diferencas = list(
            difflib.unified_diff(
                linhas_ref,
                linhas_remotas_filtradas,
                fromfile=ARQUIVO_REF,
                tofile=f"{nome}:dispositivo.cfg",
                lineterm=""
            )
        )

        if not diferencas:
            return nome, "CONFORME", []
        return nome, "NÃO CONFORME", diferencas

    except Exception as e:
        return nome, f"ERRO ({type(e).__name__}: {e})", []
    finally:
        if sftp:
            sftp.close()
        if cliente:
            cliente.close()


def main():
    with open(ARQUIVO_REF, encoding="utf-8") as f:
        linhas_ref = [linha.strip() for linha in f if linha.strip()]

    with open("inventario_chave.json", encoding="utf-8") as f:
        inventario = json.load(f)

    # Prepara o ambiente e aplica o desvio manual em R2
    preparar_cenario_laboratorio(inventario)

    linhas_relatorio = [
        "==========================================================",
        "       RELATÓRIO DE AUDITORIA DE CONFORMIDADE (DRIFT)     ",
        f"       Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "==========================================================",
    ]

    for disp in inventario:
        nome, status, diffs = auditar_dispositivo(disp, linhas_ref)
        linhas_relatorio.append(f"\nDispositivo: {nome} -> Status: [{status}]")
        if diffs:
            linhas_relatorio.append("Diferenças encontradas (- esperado | + encontrado):")
            for d in diffs:
                linhas_relatorio.append(f"  {d}")

    relatorio_final = "\n".join(linhas_relatorio)
    print(relatorio_final)

    # Salva o entregável do relatório gerado
    with open(RELATORIO_SAIDA, "w", encoding="utf-8") as f:
        f.write(relatorio_final + "\n")
    print(f"\nRelatório salvo em '{RELATORIO_SAIDA}'.")


if __name__ == "__main__":
    main()