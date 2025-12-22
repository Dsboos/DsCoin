from PySide6.QtWidgets import (QDialog, QLineEdit, QPlainTextEdit, QPushButton, QLabel, QApplication,
                               QFormLayout, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import qdarktheme
from dsc.wallet_handler.wallet_handler import WalletHandler


class DsCoinLogin(QDialog):
    def __init__(self, wallet_handler):
        super().__init__()
        self.setWindowTitle("DsCoin Login")
        self.setFixedSize(460, 580)
        self.setWindowIcon(QIcon("src\\dsc\\ui\\assets\\icons\\logo.png"))
        
        #UI Elements
        self.name_field = QLineEdit(placeholderText="Enter Wallet Name")
        self.name_field.setMaxLength(18) 
        self.name_field.setFixedWidth(180)

        self.pk_field = QPlainTextEdit(placeholderText="Enter Public Key")
        self.pk_field.setMaximumHeight(50)
        self.sk_field = QPlainTextEdit(placeholderText="Enter Private Key")
        self.sk_field.setMaximumHeight(50)

        self.add_btn = QPushButton("Add Wallet")
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.setMinimumWidth(80)
        self.add_btn.setStyleSheet(styleSheets.good_btn)
        self.add_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.error_label = QLabel("TEST ERROR TEST ERROR TEST ERROR TEST ERROR")
        self.error_label.setStyleSheet("color: crimson;")
        self.error_label.setMaximumHeight(15)

        self.del_btn = QPushButton(QIcon().fromTheme("edit-delete"), "")
        self.del_btn.setStyleSheet(styleSheets.bad_btn)
        self.del_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.wallet_list = QTableWidget()
        self.wallet_list.setColumnCount(2)
        self.wallet_list.verticalHeader().setVisible(False)
        self.wallet_list.setHorizontalHeaderLabels(["Name", "Key"])
        self.wallet_list.setColumnWidth(0, 100)
        self.wallet_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.wallet_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.wallet_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.wallet_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.wallet_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.wallet_list.setStyleSheet("font-size: 8pt")

        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedWidth(100)
        self.login_btn.setStyleSheet(styleSheets.good_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(styleSheets.bad_btn)
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        #Application Data & Connections
        self.wh = wallet_handler
        self.add_btn.clicked.connect(self.add_wallet)
        self.del_btn.clicked.connect(self.del_wallet)
        self.cancel_btn.clicked.connect(self.reject)
        self.login_btn.clicked.connect(self.open_wallet)

        #Initializations
        self.initUI()
        self.load_wallets()
        self.display_error()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(10)

        #Header
        h1 = QLabel("DsCoin Wallet")
        h1.setStyleSheet(styleSheets.header1)
        main_layout.addWidget(h1)

        b1 = QLabel("Select and log-in to a wallet from the list of added wallets. If you don't have any, add one below.")
        b1.setWordWrap(True)
        main_layout.addWidget(b1)
        main_layout.addSpacing(10)

        #Add Wallet form
        wallet_form = QFormLayout()
        h2 = QLabel("Add Wallet:")
        h2.setStyleSheet(styleSheets.header3)
        wallet_form.addRow(h2)
        wallet_form.addRow("Name: ", self.name_field)
        wallet_form.addRow("Public Key: ", self.pk_field)
        wallet_form.addRow("Private Key: ", self.sk_field)
        btn_container1 = QHBoxLayout()
        btn_container1.addWidget(self.error_label)
        btn_container1.addStretch()
        btn_container1.addWidget(self.add_btn)
        wallet_form.setLayout(4, QFormLayout.ItemRole.SpanningRole, btn_container1)

        main_layout.addLayout(wallet_form)
        main_layout.addSpacing(8)

        #Wallet Selector
        h3_container = QHBoxLayout()
        h3 = QLabel("Select Wallet:")
        h3.setStyleSheet(styleSheets.header3)
        h3_container.addWidget(h3)
        h3_container.addStretch()
        h3_container.addWidget(self.del_btn)
        main_layout.addLayout(h3_container)
        main_layout.addWidget(self.wallet_list)

        btn_container2 = QHBoxLayout()
        btn_container2.addWidget(self.cancel_btn)
        btn_container2.addStretch()
        btn_container2.addWidget(self.login_btn)
        main_layout.addLayout(btn_container2)

        self.setLayout(main_layout)

    #Functional Methods
    def load_wallets(self):
        wallets = self.wh.get_wallets()
        if not wallets:
            return
        self.wallet_list.clearContents()
        self.wallet_list.setRowCount(0)
        row = 0
        for wallet in wallets:  #(pk, sk, name)
            pk = wallet[0]
            name = wallet[2]
            self.wallet_list.insertRow(row)
            self.wallet_list.setItem(row, 0, QTableWidgetItem(name))
            self.wallet_list.setItem(row, 1, QTableWidgetItem(pk))
            row += 1
    
    def clear_form(self):
        self.name_field.setText("")
        self.pk_field.setPlainText("")
        self.sk_field.setPlainText("")
        self.display_error()

    def add_wallet(self):
        name = self.name_field.text()
        pk = self.pk_field.toPlainText().strip().replace('\n', '')
        sk = self.sk_field.toPlainText().strip().replace('\n', '')
        res, msg = self.wh.add_wallet(pk, sk, name)
        if not res:
            self.display_error(msg)
            return 
        self.load_wallets()
        self.clear_form()

    def open_wallet(self):
        selected_row =  [index.row() for index in self.wallet_list.selectedIndexes()]
        if not selected_row:
            self.display_error("Select a wallet first!")
            return
        pk = self.wallet_list.model().index(selected_row[0], 1).data()
        if not self.wh.init_user(pk):
            self.display_error("Couldn't find wallet: missing from database?")
            return
        self.accept()

    def del_wallet(self):
        selected_row =  [index.row() for index in self.wallet_list.selectedIndexes()]
        if not selected_row:
            self.display_error("Select a wallet to remove first >:O")
            return
        pk = self.wallet_list.model().index(selected_row[0], 1).data()
        reply = QMessageBox.question(self, "Remove Wallet?", 
                                     "Make sure your remember your private key!\nYour wallet (and UTXOs) will still exist after removing—you just won't be able to access it until you add it back.", 
                                     defaultButton=QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.wh.del_wallet(pk)
            self.load_wallets()
            self.display_error()
        else:
            return

    def display_error(self, msg=None):
        if not msg:
            self.error_label.setText("")
            return
        self.error_label.setText(msg)
    
class styleSheets:
    big_btn = "QPushButton {font-size: 12pt; font-weight: bold; padding: 10px;}"
    good_btn = "QPushButton:hover{background-color: green; color: white;} QPushButton:pressed{background-color: darkgreen}" 
    bad_btn = "QPushButton:hover{background-color: crimson; color: white;} QPushButton:pressed{background-color: darkred}"
    header1 = "QLabel{font-size: 18pt; font-weight: bold;}"
    header2 = "QLabel{font-size: 16pt; font-weight: bold;}"
    header3 = "QLabel{font-size: 12pt; font-weight: bold;}"

if __name__ in "__main__":
    app = QApplication()
    wh = WalletHandler()
    qdarktheme.setup_theme("dark", "rounded")
    win = DsCoinLogin(wh)
    win.show()
    app.exec()