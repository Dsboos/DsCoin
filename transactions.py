from prettyprint import warn, fail, success, info
from datetime import datetime
import random
import ecdsa
import hashlib

class TxO():
    def __init__(self, sndr, rcvr, amt, name="unnamed_output"):
        self.nonce = f"{random.randint(100000, 999999)}"
        self.name = name
        self.sndr = sndr
        self.rcvr = rcvr
        self.amt = amt
        self.hash = hashlib.sha256(self.info().encode()).hexdigest()
    
    def __repr__(self):
        return f"<O|{self.name}|{self.nonce[:4]}>"

    def info(self):
        return f"nonce: {self.nonce}||sndr: {self.sndr.to_string().hex()}||rcvr: {self.rcvr.to_string().hex()}||amt: {self.amt} DSC"

class Tx():
    def __init__(self, sndr, name="unnamed_tx"):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"

        #Tx Identification Details
        self.name = name
        self.sndr = sndr

        #Tx Verification Details
        self.signature = None
        self.hash = None

        #Tx Transfer Details
        self.inputs = []
        self.inputs_amt = 0
        self.outputs = []
        self.outputs_amt = 0
        self.tx_fee = None #Calculated and added by miners when Tx is put into a block
    
    def __repr__(self):
        return f"<Tx|{self.name}|{self.nonce[:4]}>"

    def __hash__(self):
        return int(self.hash, 16)
    
    def info(self): #Preserves unalterable information about the Tx in a string for hashing
        info = f"[{self.nonce}]\nSender: {self.sndr.to_string().hex()}\nInputs: ["
        for TxI in self.inputs:
            info += f"{TxI.hash}, "
        info += f"]\nOutputs: ["
        for TxO in self.outputs:
            info += f"{TxO.hash}, "
        info += f"]\n"
        return info

    def add_input(self, TxI):
        #Basic Verification before adding inputs, detailed verification happens at blockchain level
        if TxI.rcvr != self.sndr: 
            fail(f"[{self}] Input {TxI} not added: Doesn't belong to user!")
            return False
        #Add the input to the inputs list
        self.inputs_amt += TxI.amt
        self.inputs.append(TxI)
        success(f"[{self}] Added input {TxI}!")
        return True
    
    def create_output(self, rcvr, amt):
        #Check if amount is greater than zero
        if amt <= 0:
            fail(f"[{self}] Output {TxO} not added: Amount less than or equal to Zero!")
            return False
        output = TxO(self.sndr, rcvr, amt)
        self.outputs_amt += amt
        self.outputs.append(output)
        success(f"[{self}] Added output {output}")
        return output

    def sign(self, sk): #Generates a hash for the Tx and signs that hash
        #Verify if inputs is > outputs
        if (self.inputs_amt - self.outputs_amt) < 0:
            warn(f"[{self}] Couldn't sign: Output amount more than Input amount!")
            return False
        try:
            self.hash = hashlib.sha256(self.info().encode()).hexdigest()
            self.signature = sk.sign(self.hash.encode())
            return self.signature.hex()
        except Exception as e:
            print(e)
            warn(f"[{self}] Could not sign: Check private key!")
            return False


#Verifies the key of any hash and signature (generally reserved for Tx's and Blocks)
def verify_signature(pk, hash, signature):
    try:
        pk.verify(signature, hash.encode())
        return True
    except:
        warn(f"[Signature Verification] {hash[:10]}...: Signature could not be verified!")
        return False


if __name__ == "__main__":
    sk = ecdsa.SigningKey.generate(ecdsa.curves.SECP256k1)
    pk = sk.get_verifying_key()
    tx = Tx(pk)
    txo1_invalid = tx.create_output(pk, 0)
    txo1 = tx.create_output(pk, 0.04)
    tx.add_input(txo1)
    tx.sign(sk)
    print(tx.info())