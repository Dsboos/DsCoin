from dsc.common.prettyprint import warn, fail, success, info
from dsc.common.hashinfo import hash_info
from datetime import datetime
from functools import singledispatch
import random
import ecdsa
import hashlib

class TxO():
    def __init__(self, sndr, rcvr, amt, name="unnamed_output"):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"
        self.name = name

        #Transaction Details
        self.sndr = sndr
        self.rcvr = rcvr
        self.amt = amt
        
        self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()

        info(f"Created {self}!")
    
    def __repr__(self):
        return f"<TxO|{self.name}|{self.nonce[:4]}>"

    def __hash__(self):
        return int(self.hash, 16)


class Tx():
    def __init__(self, sndr, name="unnamed_tx"):
        #Nonce
        self.nonce = f"{random.randint(100000, 999999)}_{datetime.now().strftime("%H:%M:%S_%d/%m/%y")}"
        self.name = name

        #Tx Identification Details
        self.sndr = sndr
        self.signature = None
        self.hash = None

        #Tx Transfer Details
        self.inputs = []
        self.inputs_amt = 0
        self.outputs = []
        self.outputs_amt = 0
        self.Tx_fee = None #Calculated and added by miners when Tx is put into a block

        info(f"Created {self}!")
    
    def __repr__(self):
        return f"<Tx|{self.name}|{self.nonce[:4]}>"

    def __hash__(self):
        return int(self.hash, 16)

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
    
    def create_output(self, rcvr, amt, name="unnamed_output"):
        #Check if amount is greater than zero
        if amt <= 0:
            fail(f"[{self}] Output {TxO} not added: Amount less than or equal to Zero!")
            return False
        output = TxO(self.sndr, rcvr, amt, name=name)
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
            self.hash = hashlib.sha256(hash_info(self).encode()).hexdigest()
            self.signature = sk.sign(self.hash.encode())
            return self.signature.hex()
        except Exception as e:
            print(e)
            warn(f"[{self}] Could not sign: Check private key!")
            return False


#This function is independent of the Tx and TxO classes to prevent a malicious clone class from tampering with it
#This ensures that the hashes and/or signature of the provided class objects can be independently verified
@hash_info.register(Tx)
def _(Tx): #Compiles the unalterable information about the Tx in a string for hashing
        try:    #Sometimes malicious or classes with invalid details may throw an error
            info = f"[{Tx.nonce}]\nSender: {Tx.sndr.to_string().hex()}\nInputs: ["
            for TxI in Tx.inputs:
                info += f"{TxI.hash}, "
            info += f"]\nOutputs: ["
            for TxO in Tx.outputs:
                info += f"{TxO.hash}, "
            info += "]\n"
            return info
        except Exception as e:

            warn(f"[Hash Info] Couldn't get the info for {Tx}: {e}")
            return False
@hash_info.register(TxO)
def _(TxO):
    try:
        return f"nonce: {TxO.nonce}||sndr: {TxO.sndr.to_string().hex()}||rcvr: {TxO.rcvr.to_string().hex()}||amt: {TxO.amt} DSC"
    except Exception as e:

            warn(f"[Hash Info] Couldn't get the info for {TxO}: {e}")
            return False
    
#Verifies the key of any hash and signature (generally reserved for Tx's and Blocks)
def verify_signature(pk, hash, signature):
    try:
        pk.verify(signature, hash.encode())
        return True
    except Exception as e:
        warn(f"[Signature Verification] {hash[:10]}...: Signature could not be verified: {e}!")
        return False

#A general Tx verification tool that is trusted by blocks and blockchain
def verify_Tx(Tx):
    try:    #Malicious or invalid classes may throw errors
        #1.1- Check if the Tx is lying about its hash
        if Tx.hash != hashlib.sha256(hash_info(Tx).encode()).hexdigest():
            warn(f"[Tx Verification] {Tx} has malformed hash (was tampered with or wasn't signed properly)!")
            return False
        
        #1.2- Check if all the TxO's are not lying about their hashes. Also get the total output amt and check against what block specifies
        TxO_total = 0
        for TxO in Tx.outputs:
            if TxO.hash != hashlib.sha256(hash_info(TxO).encode()).hexdigest():
                warn(f"[Tx Verification] Output {TxO} in {Tx} has incorrect hash or was tampered with!")
                return False
            TxO_total += TxO.amt
        if TxO_total != Tx.outputs_amt:
            warn(f"[Tx Verification] {Tx} has specified incorrect output total: Actual- {TxO_total} DSC, Specified- {Tx.outputs_amt} DSC")
            return False

        #1.3- Check if all the TxI's are not lying about their hashes. Also get the total input amt and check against what block specifies
        TxI_total = 0
        for TxI in Tx.inputs:
            if TxI.hash != hashlib.sha256(hash_info(TxI).encode()).hexdigest():
                warn(f"[Tx Verification] Input {TxI} in {Tx} has incorrect hash or was tampered with!")
                return False
            TxI_total += TxI.amt
        if TxI_total != Tx.inputs_amt:
            warn(f"[Tx Verification] {Tx} has specified incorrect input total: Actual- {TxI_total} DSC, Specified- {Tx.inputs_amt} DSC")
            return False

        #2.1- Get the transaction fee if any
        Tx_fee = 0
        if Tx.Tx_fee:
            Tx_fee = Tx.Tx_fee.amt

        #2.2- Check if total input is equal to all outputs (incl. Tx fee)
        if TxI_total != (TxO_total + Tx_fee):
            warn(f"[Tx Verification] {Tx} has unbalanced inputs and outputs!")
            return False
        
        #3- Finally verify the Tx signature
        if not verify_signature(Tx.sndr, Tx.hash, Tx.signature):
            warn(f"[Tx Verification] {Tx} was not signed by specified user!")
            return False
        
        return True
    except Exception as e:
        warn(f"[Tx Verification] {Tx} encountered an error during verification: {e}!")
        return False


if __name__ == "__main__":
    sk = ecdsa.SigningKey.generate(ecdsa.curves.SECP256k1)  #Generate Private Key
    pk = sk.get_verifying_key()                             #Generate Public Key
    
    tx = Tx(pk)                                             #Create a Tx with 'pk' as initiator
    
    txo1 = tx.create_output(pk, 0.04)                       #Create an output with 0.04 DsCoins as amount.
    
    tx.sign(sk)                                             #Returns "[Tx Verification] {Tx} has unbalanced inputs and outputs!""

    print(tx.info())