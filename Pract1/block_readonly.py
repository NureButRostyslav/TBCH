import hashlib

class Block:
    def __init__(self, index, timestamp, data, previous_hash=''):
        self._index = index
        self._timestamp = timestamp
        self._data = data
        self._previous_hash = previous_hash
        self._nonce = 0
        self._hash = self.calculate_hash()
    
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