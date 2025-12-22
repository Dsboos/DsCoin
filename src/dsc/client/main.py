#Custom imports
from dsc.common.prettyprint import warn, fail, success, info
from dsc.common.transactions import TxO, Tx
from dsc.common.blocks import Block, CBTx
from dsc.node.blockchain import BlockChain
from dsc.client.wallet_handler import WalletHandler
from dsc.client.login import DsCoinLogin
from dsc.client.ui.ui import DsCoinUI
#PySide6 imports
from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QDialog
from PySide6.QtCore import QTimer, Qt
import qdarktheme
#Other imports
import random
import pickle
import ecdsa


class DsCoinClient(DsCoinUI):
    def __init__(self, wh):
        super().__init__()

        #Button Cooldowns
        #Output add cooldown
        self.add_output_cooldown = QTimer(self)
        self.add_output_cooldown.setSingleShot(True) # Timer runs only once
        self.add_output_cooldown.timeout.connect(lambda: self.add_btn.setEnabled(True))
        self.add_output_cooldown_dur = 1000 # 1 second cooldown
        
        #Connections
        self.change_wallet_btn.clicked.connect(self.change_wallet)

        self.add_btn.clicked.connect(self.add_output)
        self.remainder_btn.clicked.connect(self.add_remainder)

        self.del_tx_btn.clicked.connect(self.del_tx)
        self.clear_btn.clicked.connect(self.clear_output_form)

        # self.refresh_btn.clicked.connect()

        self.select_all_btn.clicked.connect(self.select_all_inputs)
        self.input_tx_list.itemChanged.connect(self.update_tx_data)

        #initial function calls
        self.load_output_list()
        self.load_input_list()
        self.display_error()
        self.update_qotd()

        #Application variables
        self.output_total = 0
        self.input_total = 0
        self.select_all_toggle = False

        #Wallet Handler
        self.wh = wh

    #Addition Functions
    def add_output(self):
        name = self.tx_name_field.text().strip()
        pk2 = self.pk2_field.toPlainText().strip().replace("\n", "")
        amt = self.amt_field.value()
        res, msg = wh.add_output(pk2, amt, name)
        if not res:
            self.display_error(msg)
            return
        self.load_output_list()
    
    def add_remainder(self):
        remainder = self.input_total - self.output_total
        if remainder > 0:
            self.tx_name_field.setText("Remainder Amount")
            self.pk2_field.setPlainText(wh.active_pks)
            self.amt_field.setValue(remainder)
        else:
            self.display_error("Remainder is less than or equal to Zero!")

    #Deletion Functions
    def del_tx(self):
        selected_rows =  { index.row() for index in self.output_tx_list.selectedIndexes() }
        for row in selected_rows:
            o_hash = self.output_tx_list.model().index(row, 2).data()
            wh.del_output(o_hash)
        self.load_output_list()

    def clear_output_form(self):
        self.tx_name_field.clear()
        self.pk2_field.clear()
        self.amt_field.setValue(0)
        self.display_error()    
    
    #Loading and Updating Functions
    def load_output_list(self):
        self.output_tx_list.clearContents()
        self.output_tx_list.setRowCount(0)
        outputs = wh.get_outputs()
        row = 0
        for output in outputs:
            self.output_tx_list.insertRow(row)
            self.output_tx_list.setItem(row, 0, QTableWidgetItem(output[1]))
            self.output_tx_list.setItem(row, 1, QTableWidgetItem(output[2]))
            self.output_tx_list.setItem(row, 2, QTableWidgetItem(output[3]))
            self.output_tx_list.setItem(row, 3, QTableWidgetItem(str(output[4])))   
            row += 1 
        self.update_tx_data()
    
    def load_input_list(self):
        self.input_tx_list.blockSignals(True)
        self.input_tx_list.clearContents()
        self.input_tx_list.setRowCount(0)
        inputs = wh.get_inputs()
        row = 0
        for input in inputs:
            self.input_tx_list.insertRow(row)
            self.input_tx_list.setItem(row, 0, QTableWidgetItem(input[0]))
            self.input_tx_list.setItem(row, 1, QTableWidgetItem(str(input[4])))
            checkbox_itm = QTableWidgetItem()
            checkbox_itm.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_itm.setCheckState(Qt.CheckState.Unchecked)
            self.input_tx_list.setItem(row, 2, checkbox_itm)     
            row += 1 
        self.input_tx_list.blockSignals(False)
        self.update_tx_data()

    #Utility Functions
    def change_wallet(self):
        self.setDisabled(True)
        login = DsCoinLogin(self.wh)     
        if login.exec() != QDialog.DialogCode.Accepted:
            self.setDisabled(False)
            return
        self.clear_output_form()
        self.load_input_list()
        self.load_output_list()
        self.update_qotd()
        self.setDisabled(False)

    def update_tx_data(self):
        self.output_total = 0
        self.input_total = 0
        for row in range(self.output_tx_list.rowCount()):
            self.output_total += float(self.output_tx_list.item(row, 3).text())
        self.output_amt_label.setText(f"{self.output_total:.4f}")
        for row in range(self.input_tx_list.rowCount()):
            if self.input_tx_list.item(row, 2).checkState() != Qt.CheckState.Checked:
                continue
            self.input_total += float(self.input_tx_list.item(row, 1).text())
        self.input_amt_label.setText(f"{self.input_total:.4f}")
        remainder = self.input_total - self.output_total
        self.remainder_label.setText(f"{remainder:.4f}")
        if remainder < 0:
            self.remainder_label.setStyleSheet("color: crimson; font-weight: bold;")
        else:
            self.remainder_label.setStyleSheet("font-weight: bold;")

    def select_all_inputs(self):
        if not self.select_all_toggle:
            for row in range(self.input_tx_list.rowCount()):
                self.input_tx_list.item(row, 2).setCheckState(Qt.CheckState.Checked)
        else:
            for row in range(self.input_tx_list.rowCount()):
                self.input_tx_list.item(row, 2).setCheckState(Qt.CheckState.Unchecked)
        self.select_all_toggle = not self.select_all_toggle

    def display_error(self, msg=None):
        if not msg:
            self.error_label.setText("")
            return
        self.error_label.setText(msg)

    def update_qotd(self):
        qotds = ["My wallet is like an onion—opening it makes me cry.",
                "I tried to follow a budget, but it unfollowed me back.",
                "How do you make a small fortune in finance? Start with a large one and invest wisely.",
                "A bank is a place that will lend you money if you can prove that you don't need it.",
                "If you think no one cares about you, try missing a couple of payments.",
                "The easiest way for your children to learn about money is for you not to have any.",
                "The trick is to stop thinking of it as 'your' money. \033[3m—IRS auditor",
                "Always borrow money from a pessimist. They'll never expect it back.",
                "They say money talks, but mine just waves goodbye.",
                "The safest way to double your money is to fold it over and put it in your pocket.",
                "Money is the best deodorant.",
                "What’s the use of happiness? It can’t buy you money.",]
        idx = random.randint(0,len(qotds)-1)
        self.qotd.setText(qotds[idx])
        
        
if __name__ == "__main__":
    #c1b0aaeb726af5fe5a9381364edc73876aa8e3095f4396a7709b88f6d136d9986ab79c0604de44a6028674322c78f8d47ade9f4df2744fba9949bf6183f91764
    #1bed2281877a42e0a1587fbdb5379aa8aca4468cce293b3ce565125acf00d992
    rpks = "c45678a9af9701a68e1e41ed6d36310b15ae2534d94a17f5b4ab764d5ecdd6bdfdb8bebe1fe6aad6e1330ef07a1abd909603855c93bae8f9e7f6a8a90f9a90d7"
    rsks = "73bd55e5fd8c179bfee2f662fcd2cb2663012297a35aa86784d7dcea575130dd"
    rpk =  ecdsa.VerifyingKey.from_string(bytes.fromhex(rpks), curve=ecdsa.SECP256k1)
    rsk =  ecdsa.SigningKey.from_string(bytes.fromhex(rsks), curve=ecdsa.SECP256k1)

    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    pk = sk.get_verifying_key()
    success(f"[Public Key]  {pk.to_string().hex()}")
    success(f"[Private Key] {sk.to_string().hex()}")

    app = QApplication()
    qdarktheme.setup_theme("dark", "sharp")
    wh = WalletHandler()
    login = DsCoinLogin(wh)
    if login.exec() != QDialog.DialogCode.Accepted:
        exit(1)
    win = DsCoinClient(wh)
    win.show()
    app.exec()




        