from dsc.common.transactions import TxO, Tx
import sqlite3, sys, pickle
from pathlib import Path

class MiningHandler():
    def __init__(self):
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(self.get_data_directory()/"mempool.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS pending (
                            obj BLOB,
                            tx_hash TEXT PRIMARY KEY,
                            fee REAL
                            )""")
        self.conn.commit()
                            
    def get_pending(self):
        query = self.cursor.execute("SELECT * FROM pending").fetchall()
        return query
    
    def load_pending(self, query):
        self.cursor.execute("DELETE FROM pending")
        for tx in query:
            self.cursor.execute("INSERT INTO pending VALUES(?, ?, ?)", tx)
    
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