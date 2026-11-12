import csv
import json
import conexao

# Lendo o arquivo JSON com o inventário
with open("inventario.json", "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)

# Lista de comandos (incluindo um comando inexistente conforme solicitado)
comandos = ["whoami", "hostname", "uname -r", "uptime -p"]

# O bloco 'with' do CSV deve envolver a escrita dos dados para o arquivo não fechar antes da hora
with open("inventario.csv", "w", newline="", encoding="utf-8") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)

    # O cabeçalho precisa incluir a coluna 'nome' para alinhar com as colunas de saída
    cabecalho = ["nome"] + comandos
    escritor.writerow(cabecalho)

    for maquina in dados:
        linha = []
        print(f"Conectado em {maquina['nome']}")
        
        cliente = conexao.conectar(maquina)
        linha.append(maquina["nome"])
        
        try:
            for comando in comandos:
                codigo, saida, erro = conexao.executar(cliente, comando)
                
                # Se o comando for executado com sucesso, salva a saída; se der erro, salva a mensagem de erro
                if codigo == 0:
                    resultado = saida.strip()
                else:
                    resultado = f"ERRO ({codigo}): {erro.strip()}"
                
                linha.append(resultado)

            escritor.writerow(linha)
        finally:
            # Encerra a conexão SSH com a máquina atual
            cliente.close()