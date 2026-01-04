from dsc.common.prettyprint import warn, fail, success, info
from dsc.common.transactions import TxO, Tx, verify_Tx
from dsc.common.hashinfo import hash_info
from datetime import datetime
from functools import singledispatch
import hashlib
import random
import ecdsa

#Coin Base Tx, types include: additions and miner_rewards. Additions are only authorized for testing and root block
class CBTx():
    def __init__(self, rcvr, amt, type="addition", name="unnamed_cbtx", password=None):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"
        self.name = name

        #Transaction Details
        self.rcvr = rcvr
        self.amt = amt
        self.type = type
        self.password = password

        self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()

        info(f"Created {self}!")
    
    def __repr__(self):
        return f"<CBTx|{self.name}|{self.type}|{self.nonce[:4]}>"

    def __hash__(self):
        return int(self.hash, 16)


class Block():
    def __init__(self, previous_hash, miner_pk, miner_reward=64, Tx_limit=5, difficulty=3, name="unnamed_block"):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"
        self.name = name

        #Positional Details
        self.height = 0              #The height of the block in the blockchain (set by blockchain)
        self.prevh = previous_hash   #The hash of the target this block will attach to (usually the surface block of the chain)
        self.prev = None             #The actual target obj. Not set prior to being accepted by blockchain to avoid deep copies during pickling (set by blockchain) EDIT: I DON'T THINK I EVEN USE THIS ANYMORE ANYWHERE. REFER TO RULE NUMBER ONE OF BLOCKCHAIN.
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
    
    def hash_block(self):
        return hashlib.sha256(hash_info(self).encode()).hexdigest()
    
    def add_Tx(self, Tx):
        try: #Malicious or invalid Tx can throw errors
            #Check if transaction is coin base and redirect to add_CBTx if it is:
            if isinstance(Tx, CBTx):
                return self.add_CBTx(Tx)

            #Check if this Tx is already in block
            for dscvr_Tx in self.Tx_list:
                if Tx == dscvr_Tx:
                    fail(f"[{self}] {Tx} not added: Tx already exists in block!")
                    return False
                
            #If remainder exists, add as transaction fee
            remainder = Tx.inputs_amt - Tx.outputs_amt
            if remainder > 0:
                Tx.Tx_fee = CBTx(self.miner, remainder, type="fee")

            #Verify the Tx
            if not verify_Tx(Tx):
                fail(f"[{self}] {Tx} not added: Verification failed!")
                return False

            #Reject addition if max trans limit is reached
            if len(self.Tx_list) == self.Tx_limit:
                fail(f"[{self}] {Tx} not added: Max Tx Limit Reached")
                return False

            self.Tx_list.append(Tx)
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
        self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()
        if int(self.hash, 16) <= int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',16)/16**(self.difficulty):
            return True
        return False
    
    def mine(self):
        self.add_CBTx(CBTx(self.miner, self.mine_reward, type="reward"))
        info(f"[{self}] Mining block (this may take some time)...")
        self.mine_seq = 0
        while not self.isMined():
            self.mine_seq += 1
        self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()
        success(f"[{self}] Block mined successfully with hash: {self.hash}")
        return self.hash


#This function is independent of the Block and CBTx classes to prevent a malicious clone class from tampering with it
#This ensures that the hashes of the provided class objects can be independently verified
@hash_info.register(Block)
def _(block):
    try:
        info = f"[{block.nonce}]||prev: {block.prevh}||miner: {block.miner.to_string().hex()}||mine_seq: {block.mine_seq}||\nTx's: ["
        for Tx in block.Tx_list:
            info += f"({Tx.hash}|Tx_fee: {Tx.Tx_fee.hash if Tx.Tx_fee else "None"}), "
        info += f"]\nCBTx's: ["
        for CBTx in block.CBTx_list:
            info += f"{CBTx.hash}, "
        info += "]\n"
        return info
    except Exception as e:
        
        warn(f"[Hash Info] Couldn't get the info for {block}: {e}")
        return None
@hash_info.register(CBTx)
def _(CBTx):
    try:
        return f"nonce: {CBTx.nonce}||type: {CBTx.type}||rcvr: {CBTx.rcvr.to_string().hex()}||amt: {CBTx.amt} DSC"
    except Exception as e:
        
        warn(f"[Hash Info] Couldn't get the info for {CBTx}: {e}")
        return None
    
#A general Block verification tool that is trusted by the blockchain (Verifies everything except UTxO validity)
def verify_block(block, difficulty, miner_reward, chain_password=None):
    try:#Malicious or invalid classes may throw errors
        #1.1- Check if the Block is lying about its hash
        if block.hash != hashlib.sha256(hash_info(block).encode()).hexdigest():
                warn(f"[Block Verification] {block} has malformed hash (wasn't mined properly or was tampered)!")
                return False
        
        #1.2- Verify every Tx in block (Verifies hashes, output/input balance & signature)
        for Tx in block.Tx_list:
            if not verify_Tx(Tx):
                warn(f"[Block Verification] {block} has invalid Tx: {Tx}!")
                return False
            
        #1.3 (NEW)- Verify if any inputs or outputs are repeated in block. -04/01/2026
        inputs = []
        outputs = []
        for Tx in block.Tx_list:
            for TxI in Tx.inputs:
                inputs.append(TxI.hash)
            for TxO in Tx.outputs:
                outputs.append(TxO.hash)
        if len(inputs) != len(set(inputs)):
            warn(f"[Block Verification] {block} has duplicate inputs!")
            return False
        if len(outputs) != len(set(outputs)):
            warn(f"[Block Verification] {block} has duplicate outputs!")
            return False

            
        #2.1- Check block is mined to specified difficulty
        if not (int(block.hash, 16) <= int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',16)/16**(difficulty)):
            warn(f"[Block Verification] {block} not mined to difficulty: {difficulty}!")
            return False
        
        #2.2- Check if miner reward is under specified amt, and if additions have correct password
        reward_total = 0
        for CBTx in block.CBTx_list:
            if CBTx.type == "reward":
                reward_total += CBTx.amt
            if CBTx.type == "addition":
                if CBTx.password != chain_password:
                    warn(f"[Block Verification] {block} tried unauthorized coin addition!")
                    return False
        if reward_total > miner_reward:
            warn(f"[Block Verification] {block} has awarded higher miner reward than allowed: Limit- {reward_total}, Awarded- {miner_reward}!")
            return False
        return True
    
    except Exception as e:
            
            warn(f"[Block Verification] {block} encountered an error during verification: {e}!")
            return False

if __name__ == "__main__":
    sk = ecdsa.SigningKey.generate(ecdsa.curves.SECP256k1)
    pk = sk.get_verifying_key()

    block = Block(None, pk, name="block1")
    txo1 = CBTx(pk, 150, type="addition")
    block.add_CBTx(txo1)

    
    tx_invalid1 = Tx(pk, name="invalid1")
    txi1 = TxO(pk, pk, 50, name="pk_pk_50")
    tx_invalid1.add_input(txi1)
    tx_invalid1.create_output(pk, 60, name="pk_pk_60")

    block.add_Tx(tx_invalid1)
    print(tx_invalid1.sign(sk))
    block.add_Tx(tx_invalid1)

    tx = Tx(pk, name="tx1")
    tx.add_input(txi1)
    tx.create_output(pk, 30, name="pk_pk_30")
    
    block.add_Tx(tx)
    tx.sign(sk)
    block.add_Tx(tx)
    print(hash_info(block))
    block.add_Tx(tx)