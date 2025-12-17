from dsc.utils.prettyprint import warn, fail, success, info
from dsc.blockchain.transactions import TxO, Tx
from dsc.blockchain.blocks import Block, CBTx
from dsc.blockchain.blockchain import BlockChain
from dsc.ui.ui import DsCoinUI
from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
from PySide6.QtCore import QTimer, Qt
import pickle
import sqlite3
import ecdsa


class DsCoinClient(DsCoinUI):
    def __init__(self, pk):
        super().__init__()

        self.user = pk

        #Button Cooldowns
        #Output add cooldown
        self.add_output_cooldown = QTimer(self)
        self.add_output_cooldown.setSingleShot(True) # Timer runs only once
        self.add_output_cooldown.timeout.connect(lambda: self.add_btn.setEnabled(True))
        self.add_output_cooldown_dur = 1000 # 1 second cooldown
        
        #Connections
        self.add_btn.clicked.connect(self.add_output)
        self.clear_btn.clicked.connect(self.clear_output_form)
        self.del_all_btn.clicked.connect(self.del_all_tx)
        self.del_tx_btn.clicked.connect(self.del_tx)
        self.select_all_btn.clicked.connect(self.select_all_inputs)
        self.refresh_btn.clicked.connect(self.refresh_input_list)
        self.input_tx_list.itemChanged.connect(self.read_input_list)

        #initial function calls
        self.conn, self.cursor = self.initDatabase()
        self.load_output_list()
        self.load_output_list()
        self.display_error()

        #Application variables

    def initDatabase(self):
        connection = sqlite3.connect("src/data/client.db")
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS outputs (
                    name TEXT, 
                    rcvr TEXT, 
                    o_hash TEXT PRIMARY KEY, 
                    amt REAL, 
                    obj BLOB
                    )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS inputs (
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
        #Start cooldown timer
        self.add_btn.setEnabled(False)
        self.add_output_cooldown.start(self.add_output_cooldown_dur)
        try:
            #Give default name if unnamed
            name = self.tx_name_field.text()
            if not name:
                name = "unnamed_Tx"

            #Check recipient key validity
            pk2 = convert_key(self.pk2_field.toPlainText(), "pk")
            if not pk2:
                self.display_error("Recipient's address is empty or invalid!")
                return
            
            #Check amount validity
            amt = self.amt_field.value()
            if amt == 0:
                self.display_error("Transaction amount cannot be zero ;)")
                return
            
            # #Check Private key validity
            # sk = convert_key(self.sk_field.toPlainText(), "sk")
            # if not sk:
            #     self.display_error("You forgot to add your private key, darling :3 (or you entered an invalid one oops)")
            #     self.add_btn.setEnabled(True)
            #     return

            #Create the Tx output object
            TXO = TxO(self.user, pk2, amt, name=name) #remove name=name before deployment. it is only for debugging!
            TXO_bytes = pickle.dumps(TXO)
            
            #Insert TxO into the table
            self.cursor.execute("INSERT INTO outputs VALUES (?, ?, ?, ?, ?)", 
                                (name,  TXO.rcvr.to_string().hex(), TXO.hash, amt, TXO_bytes))
            
            #Commit changes then refresh table and error message
            self.conn.commit()
            self.display_error()
            self.load_output_list()

        except Exception as e:
            self.display_error(f"{e}")
            warn(f"[Tx Creation Error] {e}")
    
    def del_all_tx(self):
        reply = QMessageBox.question(self, "Delete all transactions", 
                                     "Are you sure you want to delete all unconfirmed transactions?", 
                                     defaultButton=QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM outputs")
            self.conn.commit()
            self.load_output_list()
        else:
            return

    def del_tx(self):
        selected_rows =  { index.row() for index in self.output_tx_list.selectedIndexes() }
        print(selected_rows)
        for row in selected_rows:
            o_hash = self.output_tx_list.model().index(row, 2).data()
            print(o_hash)
            self.cursor.execute("DELETE FROM outputs WHERE o_hash = ?", (o_hash,))
        self.conn.commit()
        self.load_output_list()

    def load_output_list(self):
        self.output_tx_list.clearContents()
        self.output_tx_list.setRowCount(0)
        self.cursor.execute("SELECT * FROM outputs")
        row = 0
        for row_content in self.cursor.fetchall():
            self.output_tx_list.insertRow(row)
            self.output_tx_list.setItem(row, 0, QTableWidgetItem(row_content[0]))
            self.output_tx_list.setItem(row, 1, QTableWidgetItem(row_content[1]))
            self.output_tx_list.setItem(row, 2, QTableWidgetItem(row_content[2]))
            self.output_tx_list.setItem(row, 3, QTableWidgetItem(str(row_content[3])))   
            row += 1 
    
    def load_input_list(self):
        self.input_tx_list.clearContents()
        self.input_tx_list.setRowCount(0)
        self.cursor.execute("SELECT * FROM inputs")
        row = 0
        for row_content in self.cursor.fetchall():
            self.input_tx_list.insertRow(row)
            self.input_tx_list.setItem(row, 0, QTableWidgetItem(row_content[0]))
            self.input_tx_list.setItem(row, 1, QTableWidgetItem(row_content[1]))
            self.input_tx_list.setItem(row, 2, QTableWidgetItem(row_content[2]))
            checkbox_itm = QTableWidgetItem()
            checkbox_itm.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_itm.setCheckState(Qt.CheckState.Unchecked)
            self.input_tx_list.setItem(0, 3, checkbox_itm)     
            row += 1 

    def refresh_input_list(self):
        pass

    def read_input_list(self):
        if self.input_tx_list.item(0, 3).checkState() == Qt.CheckState.Checked:
            print("Checked")
        else:
            print("Unchecked")

    def select_all_inputs(self):
        if self.input_tx_list.item(0, 3).checkState() == Qt.CheckState.Checked:
            print("Checked")
        else:
            print("Unchecked")

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




        