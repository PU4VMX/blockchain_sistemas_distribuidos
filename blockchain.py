from multiprocessing import Process
from argparse import ArgumentParser
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from flask import Flask, jsonify, request
import requests
from flask_cors import CORS


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False
            last_block = block
            current_index += 1

        return True

    def find_consensus_block(self):
        """
        Determina o bloco de consenso baseado na presença do mesmo bloco
        em 50% + 1 dos nós da rede.
        """
        block_counts = {}
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                for block in chain:
                    block_hash = self.hash(block)
                    if block_hash not in block_counts:
                        block_counts[block_hash] = 0
                    block_counts[block_hash] += 1

        majority_count = len(self.nodes) // 2 + 1
        for block_hash, count in block_counts.items():
            if count >= majority_count:
                return block_hash

        return None

    def resolve_conflicts(self):
        """
        O algoritmo de consenso agora verifica o bloco de consenso (50% + 1 dos nós)
        e sincroniza para a cadeia mais longa que contém esse bloco.
        """
        consensus_block = self.find_consensus_block()
        if not consensus_block:
            return False

        new_chain = None
        max_length = len(self.chain)

        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                if (len(chain) > max_length and
                        any(self.hash(block) == consensus_block for block in chain) and
                        self.valid_chain(chain)):
                    max_length = len(chain)
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


def create_app():
    app = Flask(__name__)

    node_identifier = str(uuid4()).replace('-', '')
    blockchain = Blockchain()

    @app.route('/mine', methods=['GET'])
    def mine():
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block)
        blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        # Notificar os outros nós para resolver conflitos
        for node in blockchain.nodes:
            try:
                requests.get(f'http://{node}/nodes/resolve')
            except requests.exceptions.RequestException:
                pass

        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200

    @app.route('/transactions/new', methods=['POST'])
    def new_transaction():
        values = request.get_json()
        required = ['sender', 'recipient', 'amount']
        if not all(k in values for k in required):
            return 'Missing values', 400
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
        return jsonify({'message': f'Transaction will be added to Block {index}'}), 201

    @app.route('/chain', methods=['GET'])
    def full_chain():
        return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

    @app.route('/nodes/register', methods=['POST'])
    def register_nodes():
        values = request.get_json()
        nodes = values.get('nodes')
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400
        for node in nodes:
            blockchain.register_node(node)
        return jsonify({'message': 'New nodes have been added', 'total_nodes': list(blockchain.nodes)}), 201

    @app.route('/nodes/resolve', methods=['GET'])
    def consensus():
        replaced = blockchain.resolve_conflicts()
        if replaced:
            response = {'message': 'Our chain was replaced', 'new_chain': blockchain.chain}
        else:
            response = {'message': 'Our chain is authoritative', 'chain': blockchain.chain}
        return jsonify(response), 200

    return app


def run_node(port):
    app = create_app()
    CORS(app)
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    processes = []
    for port in range(5000, 5010):  # Portas de 5000 a 5009
        process = Process(target=run_node, args=(port,))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
