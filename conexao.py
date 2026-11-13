import os
import paramiko


def conectar(disp):
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    kwargs = {
        "hostname": disp["host"],
        "port": disp.get("porta", 22),
        "username": disp["usuario"],
        "look_for_keys": False,
        "allow_agent": False,
        "timeout": 5,
    }

    if "chave" in disp and disp["chave"]:
        kwargs["key_filename"] = disp["chave"]
    else:
        kwargs["password"] = os.environ.get("SSH_SENHA", "")

    cliente.connect(**kwargs)
    return cliente


def executar(cliente, comando):
    stdin, stdout, stderr = cliente.exec_command(comando)
    saida = stdout.read().decode("utf-8", errors="ignore")
    erro = stderr.read().decode("utf-8", errors="ignore")
    return stdin, saida, erro