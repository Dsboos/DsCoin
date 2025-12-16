from dsc.utils.prettyprint import warn, fail, success, info
from dsc.blockchain.transactions import TxO, Tx
from dsc.blockchain.blocks import Block, CBTx
from dsc.blockchain.blockchain import BlockChain
from dsc.ui import DsCoinUI
from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
from PySide6.QtCore import QTimer
import pickle
import sqlite3
import ecdsa


class DsCoinClient(DsCoinUI):
    def __init__(self, pk):
        super().__init__()

        self.user = pk

        #Button Cooldowns
        #Sign cooldown
        self.sign_cooldown_timer = QTimer(self)
        self.sign_cooldown_timer.setSingleShot(True) # Timer runs only once
        # self.sign_cooldown_timer.timeout.connect(lambda: self.add_btn.setEnabled(True))
        self.sign_cooldown_duration_ms = 3000 # 3 seconds cooldown
        
        #Connections
        self.add_btn.clicked.connect(self.add_output)
        self.clear_btn.clicked.connect(self.clear_output_form)
        self.del_all_btn.clicked.connect(self.del_all_tx)
        self.del_tx_btn.clicked.connect(self.del_tx)

        #initial function calls
        self.conn, self.cursor = self.initDatabase()
        self.load_output_list()
        self.display_error()

        #Application variables

    def initDatabase(self):
        connection = sqlite3.connect("src/dsc/client.db")
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS output_cache (
                    name TEXT, 
                    o_hash TEXT PRIMARY KEY, 
                    rcvr TEXT, 
                    amt REAL, 
                    obj BLOB
                    )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS input_cache (
                    o_hash TEXT PRIMARY KEY, 
                    sndr TEXT, 
                    amt REAL, 
                    obj BLOB
                    )""")
        return connection, cursor

    def clear_output_form(self):
        self.tx_name_field.clear()
        self.pk2_field.clear()
        self.amt_field.clear()
        self.sk_field.clear()
        self.display_error()    
    
    def add_output(self):
        try:
            #Give default name if unnamed
            name = self.tx_name_field.text()
            if not name:
                name = "unnamed_Tx"

            #Check recipient key validity
            pk2 = convert_key(self.pk2_field.toPlainText(), "pk")
            if not pk2:
                self.display_error("Recipient's address is empty or invalid!")
                self.add_btn.setEnabled(True)
                return
            
            #Check amount validity
            amt = self.amt_field.value()
            if amt == 0:
                self.display_error("Transaction amount cannot be zero ;)")
                self.add_btn.setEnabled(True)
                return
            
            # #Check Private key validity
            # sk = convert_key(self.sk_field.toPlainText(), "sk")
            # if not sk:
            #     self.display_error("You forgot to add your private key, darling :3 (or you entered an invalid one oops)")
            #     self.add_btn.setEnabled(True)
            #     return
            
            TXO = TxO(self.user, pk2, amt, name=name)#remove name=name before deployment. it is only for debugging!
         
            TXO_bytes = pickle.dumps(TXO)
            
            self.sign_cooldown_timer.start(self.sign_cooldown_duration_ms) # Start the cooldown timer
            self.cursor.execute("""INSERT INTO unconfirmed_tx 
                        (tx_name, tx_addr, tx_hash, tx_amt, tx_obj) 
                        VALUES(?, ?, ?, ?, ?)
                        """, (name, TXO.reciever.to_string().hex(), TXO.hash, amt, TXO_bytes))
            self.conn.commit()

            self.display_error()
            self.load_output_list()
        except Exception as e:
            self.display_error(e)
            warn(f"[Tx Creation Error] {e}")
            self.add_btn.setEnabled(True)
            return
    
    def del_all_tx(self):
        reply = QMessageBox.question(self, "Delete all transactions", 
                                     "Are you sure you want to delete all unconfirmed transactions?", 
                                     defaultButton=QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM unconfirmed_tx")
            self.conn.commit()
            self.load_output_list()
        else:
            return

    def del_tx(self):
        selected_rows =  { index.row() for index in self.output_tx_list.selectedIndexes() }
        for row in selected_rows:
            tx_hash = self.output_tx_list.model().index(row, 2).data()
            self.cursor.execute("DELETE FROM unconfirmed_tx WHERE tx_hash = ?", (tx_hash,))
        self.conn.commit()
        self.load_output_list()

    def load_output_list(self):
        self.output_tx_list.clearContents()
        self.output_tx_list.setRowCount(0)
        self.cursor.execute("SELECT * FROM unconfirmed_tx")
        row = 0
        for row_content in self.cursor.fetchall():
            self.output_tx_list.insertRow(row)
            self.output_tx_list.setItem(row, 0, QTableWidgetItem(row_content[0]))
            self.output_tx_list.setItem(row, 1, QTableWidgetItem(row_content[1]))
            self.output_tx_list.setItem(row, 2, QTableWidgetItem(row_content[2]))
            self.output_tx_list.setItem(row, 3, QTableWidgetItem(str(row_content[3])))   
            row += 1 

    def display_error(self, msg=None):
        if not msg:
            self.error_label.setText("")
            return
        self.error_label.setText(msg)


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


if __name__ == "__main__":

    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    pk = sk.get_verifying_key()
    success(f"[Public Key]  {pk.to_string().hex()}")
    success(f"[Private Key] {sk.to_string().hex()}")
    app = QApplication()
    win = DsCoinClient(pk)
    win.show()
    app.exec()




        