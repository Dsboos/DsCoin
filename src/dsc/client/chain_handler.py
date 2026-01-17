from dsc.common.transactions import TxO, Tx
import sqlite3, sys, pickle
from pathlib import Path

class ChainHandler():
    def __init__(self):
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