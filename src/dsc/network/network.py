

class Node():
    def __init__(self, blockchain):
        self.bc = blockchain

    def update_handler(self, stream):
        pass
    

#A node will have:
#List of connected clients and their respective blockchain states
#List of alternative nodes the client can switch to