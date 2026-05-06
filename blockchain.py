import hashlib
import datetime

class Block:
    def __init__(self, index, voter_id, vote, previous_hash):
        self.index = index
        self.timestamp = str(datetime.datetime.now())
        self.voter_id = voter_id
        self.vote = vote
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data = str(self.index) + self.timestamp + self.voter_id + self.vote + self.previous_hash
        return hashlib.sha256(data.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "0", "Genesis", "0")

    def get_last_block(self):
        return self.chain[-1]

    def add_vote(self, voter_id, vote):
        previous_block = self.get_last_block()
        new_block = Block(len(self.chain), voter_id, vote, previous_block.hash)
        self.chain.append(new_block)
