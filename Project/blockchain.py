import json
import os
from datetime import datetime
import hashlib

class Blockchain:
    def __init__(self, storage_path="blockchain.json"):
        self.storage_path = storage_path
        self.difficulty = 4
        # Ensure blockchain file exists
        if not os.path.exists(self.storage_path):
            self.save_to_file([self.create_genesis_block()])

    @property
    def chain(self):
        """Always load the chain from the JSON file."""
        return self.load_from_file()

    def create_genesis_block(self):
        return Block(0, str(datetime.now()), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_data):
        chain = self.chain  # load latest chain from file
        if not self.is_chain_valid(chain):
            raise Exception("The blockchain is compromised! Block was not added.")

        latest_block = chain[-1]
        new_block = Block(len(chain), str(datetime.now()), new_data, latest_block.hash)
        new_block.mine_block(self.difficulty)
        chain.append(new_block)
        self.save_to_file(chain)  # save updated chain

    def is_chain_valid(self, chain=None):
        chain = chain or self.chain
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            if current.hash != current.calculate_hash() or current.previous_hash != previous.hash:
                return False
        return True

    def save_to_file(self, chain):
        """Save the given chain to JSON."""
        data = [self.block_to_dict(block) for block in chain]
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self):
        """Load the chain from JSON."""
        with open(self.storage_path, "r") as f:
            data = json.load(f)
            return [self.block_from_dict(b) for b in data]

    def block_to_dict(self, block):
        return {
            "index": block.index,
            "timestamp": block.timestamp,
            "data": block.data,
            "previous_hash": block.previous_hash,
            "nonce": block.nonce,
            "hash": block.hash
        }

    def block_from_dict(self, data):
        b = Block.from_full_data(data["index"], data["timestamp"], data["data"], data["previous_hash"], data["nonce"], data["hash"])
        return b

    def check_integrity(self):
        return self.is_chain_valid()

    # def print_chain(self):
    #     for block in self.chain:
    #         print("Block", block.index)
    #         print("  Timestamp:", block.timestamp)
    #         print("  Data:", block.data)
    #         print("  Previous Hash:", block.previous_hash)
    #         print("  Hash:", block.hash)
    #         print("  Nonce:", block.nonce)
    #         print("-" * 40)


class Block:
    def __init__(self, index, timestamp, data, previous_hash=''):
        self._index = index
        self._timestamp = timestamp
        self._data = data
        self._previous_hash = previous_hash
        self._nonce = 0
        self._hash = self.calculate_hash()
    
    @classmethod
    def from_full_data(cls, index, timestamp, data, previous_hash, nonce, hash):
        block = cls(index, timestamp, data, previous_hash)
        block._nonce = nonce
        block._hash = hash
        return block

    @property
    def index(self):
        return self._index
    
    @property
    def timestamp(self):
        return self._timestamp
    
    @property
    def data(self):
        return self._data
    
    @property
    def previous_hash(self):
        return self._previous_hash
    
    @property
    def nonce(self):
        return self._nonce
    
    @property
    def hash(self):
        return self._hash
    

    def calculate_hash(self):
        block_string = f"{self._index}{self._timestamp}{self._data}{self._previous_hash}{self._nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        print(f"Mining block {self._index}...")
        while self._hash[:difficulty] != '0' * difficulty:
            self._nonce += 1
            self._hash = self.calculate_hash()
        print(f"Block mined: {self._hash}\n")