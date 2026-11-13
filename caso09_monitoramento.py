from datetime import datetime
import json
from conexao import conectar, executar

LIMIAR_DISCO = 80.0      # Alerta se ocupação de / > 80%
LIMIAR_LOAD = 2.0        # Alerta se load average (1 min) > 2.0


def verificar_saude(disp):
    nome = disp["nome"]
    cliente = None

    try:
        cliente = conectar(disp)

        # 1. Ocupação do disco raiz (/) em porcentagem (ex: "42")
        _, out_disco, err_disco = executar(
            cliente,
            "df -P / | awk 'NR==2 {gsub(\"%\", \"\", $5); print $5}'"
        )
        if not out_disco.strip():
            raise RuntimeError(f"Falha ao ler disco: {err_disco.strip()}")
        disco_pct = float(out_disco.strip())

        # 2. Carga média (load average de 1 minuto) a partir de /proc/loadavg
        _, out_load, err_load = executar(
            cliente,
            "awk '{print $1}' /proc/loadavg"
        )
        if not out_load.strip():
            raise RuntimeError(f"Falha ao ler /proc/loadavg: {err_load.strip()}")
        load_1m = float(out_load.strip())

        # 3. Verificação se o serviço sshd está em execução
        _, out_sshd, _ = executar(
            cliente,
            "pgrep -x sshd >/dev/null && echo ATIVO || echo INATIVO"
        )
        sshd_status = out_sshd.strip()

        # Avaliação dos limiares e classificação
        motivos = []
        if disco_pct > LIMIAR_DISCO:
            motivos.append(f"Disco alto ({disco_pct:.0f}% > {LIMIAR_DISCO:.0f}%)")
        if load_1m > LIMIAR_LOAD:
            motivos.append(f"Carga alta ({load_1m:.2f} > {LIMIAR_LOAD:.1f})")
        if sshd_status != "ATIVO":
            motivos.append("Serviço sshd inativo")

        status = "ALERTA" if motivos else "OK"

        return {
            "nome": nome,
            "status": status,
            "disco": f"{disco_pct:.0f}%",
            "load": f"{load_1m:.2f}",
            "sshd": sshd_status,
            "detalhes": "; ".join(motivos) if motivos else "Dentro dos parâmetros"
        }

    except Exception as e:
        return {
            "nome": nome,
            "status": "FALHA",
            "disco": "-",
            "load": "-",
            "sshd": "-",
            "detalhes": f"{type(e).__name__}: {e}"
        }
    finally:
        if cliente:
            cliente.close()


def exibir_painel(resultados):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    largura = 78

    print("=" * largura)
    print(f"{'PAINEL DE MONITORAMENTO NOC':^{largura}}")
    print(f"{'Atualizado em: ' + agora:^{largura}}")
    print("=" * largura)
    print(f"{'DISP':<6} | {'STATUS':<8} | {'DISCO /':<8} | {'LOAD (1m)':<10} | {'SSHD':<7} | {'OBSERVAÇÕES'}")
    print("-" * largura)

    totais = {"OK": 0, "ALERTA": 0, "FALHA": 0}

    for r in resultados:
        totais[r["status"]] = totais.get(r["status"], 0) + 1
        print(
            f"{r['nome']:<6} | "
            f"{r['status']:<8} | "
            f"{r['disco']:<8} | "
            f"{r['load']:<10} | "
            f"{r['sshd']:<7} | "
            f"{r['detalhes']}"
        )

    print("-" * largura)
    print(
        f"RESUMO: Total={len(resultados)} | "
        f"OK={totais['OK']} | "
        f"ALERTA={totais['ALERTA']} | "
        f"FALHA={totais['FALHA']}"
    )
    print("=" * largura)


def main():
    with open("inventario_chave.json", encoding="utf-8") as f:
        inventario = json.load(f)

    resultados = [verificar_saude(disp) for disp in inventario]
    exibir_painel(resultados)


if __name__ == "__main__":
    main()