from prettyprint import warn, fail, success, info
from datetime import datetime
from functools import singledispatch
import transactions
import hashlib
import random
import ecdsa

#Coin Base Tx, types include: additions and miner_rewards. Additions are only authorized for testing and root block
class CBTx():
    def __init__(self, rcvr, amt, type="addition", name="unnamed_CBTx"):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"
        self.name = name

        #Transaction Details
        self.rcvr = rcvr
        self.amt = amt
        self.type = type

        self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()

        info(f"Created {self}!")
    
    def __repr__(self):
        return f"<CBTx|{self.name}|{self.type}|{self.nonce[:4]}>"

    def __hash__(self):
        return int(self.hash, 16)


class Block():
    def __init__(self, previous_block, miner_pk, miner_reward=64, Tx_limit=5, difficulty=3, name="unnamed_block"):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"
        self.name = name

        #Positional Details
        self.height = 0              #The height of the block in the blockchain (set by blockchain)
        self.prev = previous_block   #The target this block will attach to (usually the surface block of the chain)
        self.next = []               #The blocks attached to this block (set by blockchain)
        
        #Mining Details
        self.difficulty = difficulty #Difficulty of mining the block(specified by blockchain)
        self.mine_seq = 0            #The sequence obtained in order to bring the block hash within acceptable range
        self.miner = miner_pk        #The key that recieves the miner reward and transaction fee
        self.mine_reward = miner_reward
        self.hash = None

        #Transaction Details
        self.Tx_list = []            #The list of all the Tx's currently in the block
        self.Tx_limit = Tx_limit     #The limit of how many Tx's a block is allowed to add (specified by blockchain)
        self.CBTx_list = []          #The list of all coin base transactions (additions + miner reward)
        
        info(f"Created {self}!")

    def __repr__(self):
        return f"<Block|{self.height}|{self.name}|{self.nonce[:4]}>"
    
    def __hash__(self):
        return int(self.hash, 16)
    
    def add_Tx(self, Tx):
        try: #Malicious or invalid Tx can throw errors
            #Check if transaction is coin base and redirect to add_CBTx if it is:
            if isinstance(Tx, CBTx):
                return self.add_CBTx(Tx)

            #Check if this Tx is already in block
            for dscvr_Tx in block.Tx_list:
                if Tx == dscvr_Tx:
                    fail(f"[{self}] {Tx} not added: Tx already exists in block!")
                    return False
                
            #If remainder exists, add as transaction fee
            remainder = Tx.inputs_amt - Tx.outputs_amt
            if remainder > 0:
                Tx.Tx_fee = CBTx(self.miner, remainder, type="fee")

            #Verify the Tx
            if not transactions.verify_Tx(Tx):
                fail(f"[{self}] {Tx} not added: Verification failed!")
                return False

            #Reject addition if max trans limit is reached
            if len(self.Tx_list) == self.Tx_limit:
                fail(f"[{self}] {Tx} not added: Max Tx Limit Reached")
                return False

            block.Tx_list.append(Tx)
            success(f"[{self}] added {Tx} with Tx Fee: {remainder}")
            return True
        except Exception as e:
            fail(f"[{self}] {Tx} not added: Encountered an Error: {e}")
            return False
        
    def add_CBTx(self, CBTx):
        try:
            if CBTx.type == "addition" or CBTx.type == "reward": #Remove the "addition" condition before deployment
                self.CBTx_list.append(CBTx)
                return True
            fail(f"[{self}] {CBTx} not added: Invalid type!")
            return False
        except Exception as e:
            fail(f"[{self}] {CBTx} not added: Encountered an Error: {e}")
            return False

    def isMined(self):
        block_hash = hashlib.sha256(hash_info(self).encode()).hexdigest()
        if int(block_hash, 16) <= int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',16)/16**(self.difficulty):
            return True
        return False
    
    def mine_block(self):
        self.add_CBTx(CBTx(self.miner, self.mine_reward, type="reward"))
        while not self.isMined():
            self.mine_seq += 1
        self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()
        return self.hash

def verify_block_hash(block, difficulty):
    true_hash = hashlib.sha256(block.info().encode()).hexdigest()
    stated_hash = block.hash
    if true_hash != stated_hash:
        warn(f"[Block Hash Verification] {block} was modified or hashed incorrectly!")
        return False
    if int(true_hash, 16) > int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',16)/16**(difficulty):
        warn(f"[Block Hash Verification] {block} not mined to required difficulty!")
        return False
    return True

#This function is independent of the Block and CBTx classes to prevent a malicious clone class from tampering with it
#This ensures that the hashes of the provided class objects can be independently verified
@singledispatch
def hash_info(block):
    try:
        info = f"[{block.nonce}]||prev: {block.prev.hash if block.prev else "None"}||miner: {block.miner.to_string().hex()}||mine_seq: {block.mine_seq}||\nTx's: ["
        for Tx in block.Tx_list:
            info += f"({Tx.hash}|Tx_fee: {Tx.Tx_fee.hash if Tx.Tx_fee else "None"}), "
        info += f"]\nCBTx's: ["
        for CBTx in block.CBTx_list:
            info += f"{CBTx.hash}, "
        info += "]\n"
        return info
    except Exception as e:
        warn(f"[Hash Info] Couldn't get the info for {block}: {e}")
        return False
@hash_info.register(CBTx)
def _(CBTx):
    try:
        return f"nonce: {CBTx.nonce}||type: {CBTx.type}||rcvr: {CBTx.rcvr.to_string().hex()}||amt: {CBTx.amt} DSC"
    except Exception as e:
        warn(f"[Hash Info] Couldn't get the info for {CBTx}: {e}")
        return False

if __name__ == "__main__":
    sk = ecdsa.SigningKey.generate(ecdsa.curves.SECP256k1)
    pk = sk.get_verifying_key()

    block = Block(None, pk, name="block1")
    txo1 = CBTx(pk, 150, type="addition")
    block.add_CBTx(txo1)

    
    tx_invalid1 = transactions.Tx(pk, name="invalid1")
    txi1 = transactions.TxO(pk, pk, 50, name="pk_pk_50")
    tx_invalid1.add_input(txi1)
    tx_invalid1.create_output(pk, 60, name="pk_pk_60")

    block.add_Tx(tx_invalid1)
    print(tx_invalid1.sign(sk))
    block.add_Tx(tx_invalid1)

    tx = transactions.Tx(pk, name="tx1")
    tx.add_input(txi1)
    tx.create_output(pk, 30, name="pk_pk_30")
    
    block.add_Tx(tx)
    tx.sign(sk)
    block.add_Tx(tx)
    print(hash_info(block))
    block.add_Tx(tx)
