import dsc.blockchain.blockchain
from dsc.blockchain.transactions import TxO
from dsc.utils.prettyprint import warn, fail, success, info
import pickle
import sqlite3
import ecdsa

#This module handles the client's wallets and their functionalities
#The wallet id is synonymous with user key
class WalletHandler():
    def __init__(self, first_pks):
        #Session Initialization
        self.active_pks = first_pks                     #The user key (string) who is currently handling the client (their data is displayed)
        self.active_pk = self.convert_key(first_pks, "pk")    #The key object of that active user, used for signing and verifications
        if not self.active_pk:                          #Keeping string of user key is useful to retrieve user data from tables
            warn("[Wallet Handler] Couldn't initialize wallet handler: Invalid user key!")
            return False
        self.add_wallet(self.active_pks)                #The table that stores all wallets logged into the client

        # Connections initialization
        self.init_db()
        self.connect_blockchain_db()

    #Initialization Functions
    def init_db(self):
        self.conn = sqlite3.connect("data/client.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS wallets (
                            wallet_id TEXT PRIMARY KEY
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS outputs (
                            wallet_id TEXT,
                            name TEXT, 
                            rcvr TEXT, 
                            o_hash TEXT PRIMARY KEY, 
                            amt REAL, 
                            obj BLOB                            
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS inputs (
                            walled_id TEXT,
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
        query = self.cursor.execute("SELECT * FROM wallets WHERE wallet_id = ?", (user,)).fetchone()
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
        query = self.cursor.execute("SELECT * FROM outputs WHERE wallet_id = ?", (self.active_pks,)).fetchall()
        return query
    
    def get_inputs(self):
        #Fetch and return all UTxOs belonging to the user from blockchain.db
        query = self.bc_cursor.execute("SELECT * FROM UTxOs WHERE rcvr = ?", (self.active_pks,)).fetchall()
        return query

    #Addition Functions
    def add_output(self, pk2s, amt, name=None):
        try:
            #Give default name if unnamed
            if not name:
                name = "unnamed_TxO"

            #Check recipient key validity
            pk2 = self.convert_key(pk2s, "pk")
            if not pk2:
                return False, "Recipient's address is empty or invalid!"
            
            #Check amount validity
            if amt == 0:
                return False, "Transaction amount cannot be zero ;)"
            
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

    def add_wallet(self, user_pks):
        user_pk = self.convert_key(user_pks, "pk")    #Check that the provided key string is a valid public key
        if user_pk:
            self.cursor.execute("INSERT OR IGNORE INTO wallets VALUES (?)", (user_pks,))
            return True
        warn("[Wallet] Couldn't add the wallet!")
        return False
    
    #Deletion Functions

    #Utility Functions
    def convert_key(key, type):
        try:
            if type=="pk":
                return ecdsa.VerifyingKey.from_string(bytes.fromhex(key), curve=ecdsa.SECP256k1)
            if type=="sk":
                return ecdsa.SigningKey.from_string(bytes.fromhex(key), curve=ecdsa.SECP256k1)
            return key
        except:
            warn("[Key Converter] pk or sk is invalid!")
            return False