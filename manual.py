import requests

# Configuração base
base_url = "http://127.0.0.1"

# Função para realizar a requisição
def make_request(method, url, json=None):
    try:
        if method == "POST":
            response = requests.post(url, json=json)
        elif method == "GET":
            response = requests.get(url)
        else:
            print(f"Método {method} não suportado.")
            return

        print(f"Requisição para {url} retornou {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Erro ao realizar requisição para {url}: {e}")

# Menu de ações
def menu():
    print("\nEscolha uma ação:")
    print("1. Registrar nós")
    print("2. Criar transação")
    print("3. Minerar bloco")
    print("4. Verificar cadeia")
    print("5. Resolver conflitos")
    print("6. Sair")
    return input("Digite o número da ação: ")

# Loop principal
while True:
    action = menu()

    if action == "1":
        port = input("Digite a porta do nó para registrar: ")
        nodes = input("Digite as URLs dos outros nós (separadas por vírgula): ").split(",")
        make_request("POST", f"{base_url}:{port}/nodes/register", json={"nodes": nodes})

    elif action == "2":
        port = input("Digite a porta do nó para criar a transação: ")
        sender = input("Digite o remetente: ")
        recipient = input("Digite o destinatário: ")
        amount = float(input("Digite o valor: "))
        transaction = {"sender": sender, "recipient": recipient, "amount": amount}
        make_request("POST", f"{base_url}:{port}/transactions/new", json=transaction)

    elif action == "3":
        port = input("Digite a porta do nó para minerar: ")
        make_request("GET", f"{base_url}:{port}/mine")

    elif action == "4":
        port = input("Digite a porta do nó para verificar a cadeia: ")
        make_request("GET", f"{base_url}:{port}/chain")

    elif action == "5":
        port = input("Digite a porta do nó para resolver conflitos: ")
        make_request("GET", f"{base_url}:{port}/nodes/resolve")

    elif action == "6":
        print("Encerrando o programa.")
        break

    else:
        print("Ação inválida. Tente novamente.")
