from blockchain import Blockchain

bc = Blockchain()

bc.add_vote("101", "Alice")
bc.add_vote("102", "Bob")

for block in bc.chain:
    print(block.index, block.vote, block.hash)
