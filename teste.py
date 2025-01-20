import requests
import time

# Configuração das portas dos nós
ports = ["5000", "5001", "5002"]

# URLs para as requisições
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

# Registrar nós
print("Registrando nós...")
for port in ports:
    other_nodes = [f"{base_url}:{p}" for p in ports if p != port]
    make_request(
        "POST", 
        f"{base_url}:{port}/nodes/register", 
        json={"nodes": other_nodes}
    )
    time.sleep(2)  # Aguardar 2 segundos entre as requisições

# Criar transações
print("Criando transações...")
transactions = [
    {"sender": "Pedro", "recipient": "Paulo", "amount": 5},
    {"sender": "Joao", "recipient": "Pedro", "amount": 10},
    {"sender": "Ana", "recipient": "Maria", "amount": 20},
]
for port, transaction in zip(ports, transactions):
    make_request(
        "POST", 
        f"{base_url}:{port}/transactions/new", 
        json=transaction
    )
    time.sleep(2)

# Mineração em cada nó
print("Mineração...")
for port in ports:
    make_request("GET", f"{base_url}:{port}/mine")
    time.sleep(2)

# Obter a cadeia de cada nó
print("Verificando cadeia...")
for port in ports:
    make_request("GET", f"{base_url}:{port}/chain")
    time.sleep(2)

# Resolver conflitos em cada nó
print("Resolvendo conflitos...")
for port in ports:
    make_request("GET", f"{base_url}:{port}/nodes/resolve")
    time.sleep(2)
