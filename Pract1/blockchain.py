import time
from datetime import datetime

class Blockchain:
    def __init__(self, readonly: bool):
        if readonly:
            from block_readonly import Block
        else:
            from block_readwrite import Block
        self.Block = Block

        self.chain = [self.create_genesis_block()]
        self.difficulty = 4  # Кількість нулів у хеші для PoW

    def create_genesis_block(self):
        return self.Block(0, str(datetime.now()), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_data):
        if not self.is_chain_valid():
            raise Exception("The blockchain is compromised! Block was not added.")
            
        latest_block = self.get_latest_block()
        new_block = self.Block(len(self.chain), str(datetime.now()), new_data, latest_block.hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if (current.hash != current.calculate_hash() or
                current.previous_hash != previous.hash):
                return False

        return True

    def print_chain(self):
        for block in self.chain:
            print("Block", block.index)
            print("  Timestamp:", block.timestamp)
            print("  Data:", block.data)
            print("  Previous Hash:", block.previous_hash)
            print("  Hash:", block.hash)
            print("  Nonce:", block.nonce)
            print("-" * 40)