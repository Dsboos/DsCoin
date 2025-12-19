import dsc.blockchain.blockchain
from dsc.blockchain.transactions import TxO
from dsc.utils.prettyprint import warn, fail, success, info
import pickle
import sqlite3
import ecdsa

#This module handles the client's wallets and their functionalities
#The wallet id is synonymous with user key
class WalletHandler():
    def __init__(self):
        #Session Initialization
        self.active_pks = None                     #The user key (string) who is currently handling the client (their data is displayed)
        self.active_pk = None                      #The key object of that active user, used for signing and verifications

        # Connections initialization
        self.bc_conn = None
        self.bc_cursor = None
        self.init_db()
        self.connect_blockchain_db()

    #Initialization Functions
    def init_user(self, pk):
        query = self.cursor.execute("SELECT pk FROM wallets WHERE pk = ?", (pk,)).fetchone()
        if query:
            self.active_pks = query[0]
            self.active_pk = self.convert_key(self.active_pks, "pk")
            return True
        return False

    def init_db(self):
        self.conn = sqlite3.connect("data/client.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS wallets (
                            pk TEXT PRIMARY KEY,
                            sk TEXT,
                            name TEXT
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS outputs (
                            pk TEXT,
                            name TEXT, 
                            rcvr TEXT, 
                            o_hash TEXT PRIMARY KEY, 
                            amt REAL, 
                            obj BLOB                            
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS inputs (
                            pk TEXT,
                            o_hash TEXT PRIMARY KEY, 
                            sndr TEXT, 
                            amt REAL, 
                            obj BLOB
                            )""")
        
    def connect_blockchain_db(self):
        if self.bc_conn:
            self.bc_conn.close()
        # Open a connection to the blockchain database in read-only mode
        self.bc_conn = sqlite3.connect("file:data/blockchain.db?mode=ro", uri=True) 
        self.bc_cursor = self.bc_conn.cursor()

    #Session Management Functions
    def change_user(self, user):
        query = self.cursor.execute("SELECT pk FROM wallets WHERE pk = ?", (user,)).fetchone()
        if query:                               #Check if user is already has a wallet in the database
            self.active_pks = user              #Make this user the new active user
            self.active_pk = self.convert_key(self.active_pks, "pk")
            return True
        else:
            warn("[Wallet] Couldn't find specified user!")
            return False
        pass

    #Fetching Functions
    def get_outputs(self):
        #Fetch and return all unsigned outputs stored in client.db
        query = self.cursor.execute("SELECT * FROM outputs WHERE pk = ?", (self.active_pks,)).fetchall()
        return query
    
    def get_inputs(self):
        #Fetch and return all UTxOs belonging to the user from blockchain.db
        query = self.bc_cursor.execute("SELECT * FROM UTxOs WHERE rcvr = ?", (self.active_pks,)).fetchall()
        return query
    
    def get_wallets(self):
        #Fetch and return all wallets
        query = self.cursor.execute("SELECT * FROM wallets").fetchall()
        return query

    #Addition Functions
    def add_output(self, pk2s, amt, name=None):
        try:
            #Give default name if unnamed
            if not name:
                name = "Unnamed_TxO"

            #Check recipient key validity
            pk2 = self.convert_key(pk2s, "pk")
            if not pk2:
                return False, "Recipient's address is empty or invalid!"
            
            #Check amount validity
            if amt == 0:
                return False, "Transaction amount CANNOT be zeroooo >:O"
            
            #Create the Tx output object
            TXO = TxO(self.active_pk, pk2, amt, name=name) #remove name=name before deployment. it is only for debugging!
            TXO_bytes = pickle.dumps(TXO)
            
            #Insert TxO into the table
            self.cursor.execute("INSERT INTO outputs VALUES (?, ?, ?, ?, ?, ?)", 
                                (self.active_pks, name, TXO.rcvr.to_string().hex(), TXO.hash, amt, TXO_bytes))
            
            #Commit changes
            self.conn.commit()
            return True, None
        except Exception as e:
            warn(f"[Wallet Handler] Output addition error: {e}")
            return False, "Something went wrong!"

    def add_wallet(self, user_pks, user_sks, name):
        user_pk = self.convert_key(user_pks, "pk")    #Check that the provided key string is a valid public key
        user_sk = self.convert_key(user_sks, "sk")    #Check that the provided key string is a valid private key
        if not user_pk:
            return False, "Invalid or empty public key :/"
        if not user_sk:
            return False, "Invalid or empty private key! How tf can I know if it's you??!"
        if not self.verify_key_pair(user_pk, user_sk):
            return False, "Private key don't match the public key dawg :O"
        if self.cursor.execute("SELECT * FROM wallets WHERE pk= ?", (user_pks,)).fetchall():
            return False, "You already have that wallet added, my love <3"
        self.cursor.execute("INSERT OR IGNORE INTO wallets VALUES (?, ?, ?)", (user_pks, user_sks, name if name else "Unnamed Wallet"))
        self.active_pk = user_pk
        self.active_pks = user_pks
        self.conn.commit()
        return True, None
    
    #Deletion Functions
    def del_output(self, o_hash):
        self.cursor.execute("DELETE FROM outputs WHERE o_hash = ?", (o_hash,))
        self.conn.commit()

    #Utility Functions
    def convert_key(self, key, type):
        key.strip("\n")
        try:
            if type=="pk":
                return ecdsa.VerifyingKey.from_string(bytes.fromhex(key), curve=ecdsa.SECP256k1)
            if type=="sk":
                return ecdsa.SigningKey.from_string(bytes.fromhex(key), curve=ecdsa.SECP256k1)
            return key
        except:
            warn("[Wallet Handler] pk or sk is invalid!")
            return False
    
    def verify_key_pair(self, pk, sk):
        msg = b"Repeat after me: abrar is really hot."
        signature = sk.sign(msg)
        try:
            pk.verify(signature, msg)
            return True
        except Exception as e:
            warn(f"[Wallet Handler] Couldn't verify key pair: {e}")
            return False

    

if __name__ == "__main__":
    wh = WalletHandler()
    pks = "a4b1e2d02e2bcdcb992935c1766d9ddc91ec4b84bc0e29d9875201115b4120aa25985be437e7cfd7fa9d822d7800eb3f926d38c1ce87969a738fb12ab1cabb2f"
    sks = "19c9223e178a6d39c067f107fc1899ff34ae014bcde09c0b6456bd77e8b14473"

