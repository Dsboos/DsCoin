from dsc.common.transactions import TxO, Tx
import sqlite3, sys, pickle
from pathlib import Path

class Mempool():
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
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS spent_inputs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            o_hash TEXT,
                            tx_hash TEXT
                            )""")
        self.conn.commit()
                            
    def add_tx(self, tx: Tx):
        txh = tx.hash
        fee = tx.inputs_amt - tx.outputs_amt
        self.del_tx(tx)
        self.cursor.execute("INSERT OR IGNORE INTO pending VALUES(?, ?, ?)", (pickle.dumps(tx), txh, fee))
        for input in tx.inputs:
            self.cursor.execute("INSERT OR IGNORE INTO spent_inputs VALUES(?, ?, ?)", (None, input.hash, txh))
        self.conn.commit()

    def del_tx(self, tx: Tx):
        invalid_txs = []
        for input in tx.inputs:
            query = self.cursor.execute("SELECT tx_hash FROM spent_inputs WHERE o_hash = ?", (input.hash,)).fetchall()
            for invtx in query:
                if invtx[0] not in invalid_txs:
                    invalid_txs.append(invtx[0])
            self.cursor.execute("DELETE FROM spent_inputs WHERE o_hash = ?", (input.hash,))
        for invtx in invalid_txs:
            self.cursor.execute("DELETE FROM pending WHERE tx_hash = ?", (invtx,))
            self.cursor.execute("DELETE FROM spent_inputs WHERE tx_hash = ?", (invtx,))
        self.conn.commit()

    def get_pending(self):
        query = self.cursor.execute("SELECT * FROM pending").fetchall()
        return query
    
    def get_data_directory(self):
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
        else:
            root = Path(__file__).resolve().parent
        data_directory = root / "data"
        data_directory.mkdir(parents=True, exist_ok=True)
        return data_directory
    
if __name__ == "__main__":
    # mp = Mempool()
    # txb = mp.cursor.execute("SELECT obj FROM pending").fetchone()[0]
    # tx = pickle.loads(txb)
    # print(tx.hash)
    # mp.del_tx(tx)
    pass