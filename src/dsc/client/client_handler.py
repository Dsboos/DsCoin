from dsc.common.transactions import TxO, Tx
from dsc.common.prettyprint import warn, info, fail, success
from dsc.client.node_client import NodeClient
import sqlite3, sys, pickle, asyncio, ecdsa
from pathlib import Path

db_lock = asyncio.Lock()

#This class handles the client's wallets and their functionalities
#The wallet id is synonymous with user key
class WalletHandler():
    def __init__(self, nc: NodeClient):
        #Session Initialization
        self.active_pks = None                     #The user key (string) who is currently handling the client (their data is displayed)
        self.active_pk = None                      #The key object of that active user, used for signing and verifications
        self.active_sks = None
        self.active_sk = None 

        self.nc = nc

        # Connections initialization
        self.init_db()

        #Update loop
        self.update_loop = None
        self.update_loop_running = False

    #Initialization Functions
    def init_user(self, pk):
        query = self.cursor.execute("SELECT * FROM wallets WHERE pk = ?", (pk,)).fetchone()
        if query:
            self.active_pks = query[0]
            self.active_pk = self.convert_key(self.active_pks, "pk")
            self.active_sks = query[1]
            self.active_sk = self.convert_key(self.active_sks, "sk")
            return True
        return False

    def init_db(self):
        self.conn = sqlite3.connect(self.get_data_directory()/"client.db")
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
                            rcvr TEXT,
                            amt REAL,
                            obj BLOB
                            )""")
        
    #Session Management Functions
    def change_user(self, user):
        query = self.cursor.execute("SELECT * FROM wallets WHERE pk = ?", (user,)).fetchone()
        if query:                               #Check if user is already has a wallet in the database
            self.active_pks = user              #Make this user the new active user
            self.active_pk = self.convert_key(self.active_pks, "pk")
            self.active_sks = query[1]
            self.active_sk = self.convert_key(self.active_sks, "sk")
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
    
    async def fetch_inputs(self):
        #Fetch and return all UTxOs belonging to the user from blockchain.db
        query, status = await self.nc.fetch_utxos(self.active_pks)
        return query, status
    
    async def update_inputs(self):
        query, status = await self.fetch_inputs()
        if status==200:
            async with db_lock:
                self.cursor.execute("DELETE FROM inputs")
                for row in query:
                    self.cursor.execute("INSERT INTO inputs VALUES (?, ?, ?, ?, ?)",
                                        (self.active_pks, row[0], row[3], row[4], row[5]))
                self.conn.commit()
            return True, None
        return False, status
    
    def get_inputs(self):
        query = self.cursor.execute("SELECT * FROM inputs WHERE pk = ?", (self.active_pks,)).fetchall()
        return query
    
    def get_input_from_hash(self, hash):
        query = self.cursor.execute("SELECT * FROM inputs WHERE o_hash = ?", (hash,)).fetchone()
        return query
    
    def get_output_from_hash(self, hash):
        query = self.cursor.execute("SELECT * FROM outputs WHERE o_hash = ?", (hash,)).fetchone()
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

        self.cursor.execute("INSERT OR IGNORE INTO wallets VALUES (?, ?, ?)", (user_pk.to_string().hex(), user_sk.to_string().hex(), name if name else "Unnamed Wallet"))
        self.conn.commit()
        self.active_pk = user_pk
        self.active_pks = user_pk.to_string().hex() #Notice how we don't use user_pks or user_sks directly. This is because I had discovered that sometimes keys in hex string formats have prefixes that get stripped by ecdsa, causing mismatches in my databases.
        self.active_sks = user_sk.to_string().hex()
        self.active_sk = user_sk
        return True, None
    
    #Deletion Functions
    def del_output(self, o_hash):
        self.cursor.execute("DELETE FROM outputs WHERE o_hash = ?", (o_hash,))
        self.conn.commit()

    def del_all_outputs(self):
        self.cursor.execute("DELETE FROM outputs WHERE pk = ?", (self.active_pks,))
        self.conn.commit()

    def del_wallet(self, pks):
        self.cursor.execute("DELETE FROM outputs WHERE pk = ?", (pks,))
        self.cursor.execute("DELETE FROM inputs WHERE pk = ?", (pks,))
        self.cursor.execute("DELETE FROM wallets WHERE pk = ?", (pks,))
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
     
    def get_data_directory(self):
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
        else:
            root = Path(__file__).resolve().parent
        data_directory = root / "data"
        data_directory.mkdir(parents=True, exist_ok=True)
        return data_directory
    
#This class handles everythin other than the wallet
class ClientHandler(WalletHandler):
    def __init__(self, nc):
        super().__init__(nc=nc)
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(self.get_data_directory()/"client.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS pending (
                            obj BLOB,
                            tx_hash TEXT PRIMARY KEY,
                            fee REAL
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS blockchain(
                            name TEXT,
                            height INTEGER,
                            rooth TEXT PRIMARY KEY,
                            root BLOB,
                            surface BLOB,
                            difficulty INTEGER,
                            tx_limit INTEGER,
                            mine_reward INTEGER
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS blocks (
                            hash TEXT PRIMARY KEY,
                            prevh TEXT,
                            height INTEGER,
                            main_chain BOOLEAN,
                            obj BLOB
                            )                           
                            """)
        self.conn.commit()
    
    def get_blocks(self):
        query = self.cursor.execute("SELECT * FROM blocks").fetchall()
        return query
    
    def get_block_from_hash(self, blockh):
        query = self.cursor.execute("SELECT * FROM blocks WHERE hash = ?", (blockh,)).fetchone()
        return query
    
    def load_blocks(self, query):
        self.cursor.execute("DELETE FROM blocks")
        for block in query:
            self.cursor.execute("INSERT INTO blocks VALUES (?, ?, ?, ?, ?)", block)
                            
    def get_pending(self):
        query = self.cursor.execute("SELECT * FROM pending").fetchall()
        return query
    
    def get_tx_from_hash(self, hash):
        query = self.cursor.execute("SELECT * FROM pending WHERE tx_hash = ?", (hash,)).fetchone()
        return query
    
    def load_pending(self, query):
        self.cursor.execute("DELETE FROM pending")
        for tx in query:
            self.cursor.execute("INSERT INTO pending VALUES(?, ?, ?)", tx)
    
    def get_chainstate(self):
        query = self.cursor.execute("SELECT * FROM blockchain").fetchone()
        return query
    
    def load_chainstate(self, query):
        self.cursor.execute("DELETE FROM blockchain")
        self.cursor.execute("INSERT INTO blockchain VALUES (?, ?, ?, ?, ?, ?, ?, ?)", query)

    def get_data_directory(self):
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
        else:
            root = Path(__file__).resolve().parent
        data_directory = root / "data"
        data_directory.mkdir(parents=True, exist_ok=True)
        return data_directory
    
if __name__ == "__main__":
    pass