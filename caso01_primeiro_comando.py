import json
import conexao

with open('inventario.json','r') as arquivo:
    dados=json.load(arquivo)

cliente=conexao.conectar(dados[0])

comandos=["whoami","hostname","uptime -p"]


for comando in comandos:
    codigo,saida,erro=conexao.executar(cliente,comando)
    print(f"Comando: {comando}")
    print(f"Codigo: {codigo}")
    print(f"Saida: {saida}")
    print(f"------------------")

#codigo,saida,erro=conexao.executar(cliente,"whoami")

#print(codigo)
#print(saida)
#print(erro)

#codigo2,saida2,erro=conexao.executar(cliente,"hostname")

#print("Hostname:", saida)
#print("Erro:", erro)

#codigo3,saida3,erro=conexao.executar(cliente,"uptime -p")

#print("Uptime:", saida)
#print("Erro:", erro)