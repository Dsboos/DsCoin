from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QTextEdit, QPlainTextEdit,
                               QLineEdit, QPushButton, QTableWidget, QHBoxLayout, QLayout,
                               QVBoxLayout, QGridLayout, QTabBar, QFormLayout, QSpacerItem,
                               QTabWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSizePolicy, 
                               QMessageBox, QDoubleSpinBox, QStyle, QMainWindow, QAbstractItemView)
from PySide6.QtCore import Qt, QLocale, QSize
from PySide6.QtGui import QDoubleValidator, QIcon, QAction
import qdarktheme
import sys

class DsCoinUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DsCoin Client v0.1.0")
        self.setWindowIcon(QIcon("src\\dsc\\ui\\assets\\icons\\logo.png"))
        self.resize(1080, 720)
        self.setMinimumSize(920, 600)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.menu = QWidget()
        self.setMenuWidget(self.menu)

        self.wallet_tab = QWidget()
        self.mine_tab = QWidget()
        self.blockchain_tab = QWidget()
        
        self.tab_widget.addTab(self.wallet_tab, QIcon("src\\dsc\\client\\ui\\assets\\icons\\wallet.png"),"My Wallet")
        self.tab_widget.addTab(self.mine_tab, QIcon("src\\dsc\\client\\ui\\assets\\icons\\pickaxe.png"), "Mine Blocks")
        self.tab_widget.addTab(self.blockchain_tab, QIcon("src\\dsc\\client\\ui\\assets\\icons\\blockchain.png"), "View Blockchain")
        self.tab_widget.tabBar().setMinimumWidth(500)
        self.tab_widget.setStyleSheet("QTabBar::tab {padding-left: 20px; padding-right: 20px;}")

        self.init_wallet_tab()
        self.init_menu()

    def init_wallet_tab(self):
        #============================================UI Elements============================================
        self.output_tx_label = QLabel("Output Transactions")
        self.output_tx_label.setStyleSheet(styleSheets.header2)

        self.del_tx_btn = QPushButton(QIcon.fromTheme("edit-delete"), "")
        self.del_tx_btn.setStyleSheet(styleSheets.bad_btn)
        self.del_tx_btn.setMaximumWidth(100)

        self.output_tx_list = QTableWidget()
        self.output_tx_list.setColumnCount(4)
        self.output_tx_list.verticalHeader().setVisible(False)
        self.output_tx_list.setHorizontalHeaderLabels(["Name", "Reciever Address", "Hash", "Amount\n(DSC)"])
        self.output_tx_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.output_tx_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.output_tx_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.output_tx_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.output_tx_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output_tx_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.output_tx_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.output_tx_list.setStyleSheet("font-size: 8pt")

        self.create_tx_label = QLabel("Create Transaction Output")
        self.create_tx_label.setStyleSheet(styleSheets.header3)

        self.tx_name_field = QLineEdit(placeholderText="Enter Name")
        self.tx_name_field.setMaxLength(18)
        self.tx_name_field.setFixedWidth(180)
        self.pk2_field = QPlainTextEdit(placeholderText="Enter Public Key")
        self.pk2_field.setMaximumHeight(50)
        self.amt_field = QDoubleSpinBox()
        self.amt_field.setRange(0.0, 1000000.0)
        self.amt_field.setDecimals(4)
        self.amt_field.setMaximumWidth(150)
        self.remainder_btn = QPushButton("Add Remainder")
        self.remainder_btn.setMaximumWidth(100)

        self.error_label = QLabel("Test Error Test Error 1234 1234")
        self.error_label.setStyleSheet("color: crimson;")
        self.add_btn = QPushButton("Add Output")
        self.add_btn.setStyleSheet(styleSheets.good_btn)
        self.clear_btn = QPushButton("Clear All")

        self.input_tx_label = QLabel("Input Transactions")
        self.input_tx_label.setStyleSheet(styleSheets.header2)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMaximumWidth(100)
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon.fromTheme("system-reboot"))

        self.input_tx_list = QTableWidget()
        self.input_tx_list.setColumnCount(3)
        self.input_tx_list.verticalHeader().setVisible(False)
        self.input_tx_list.setHorizontalHeaderLabels(["Hash", "Amount\n(DSC)", "Select"])
        self.input_tx_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.input_tx_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.input_tx_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.input_tx_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.input_tx_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_tx_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.input_tx_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.input_tx_list.setStyleSheet("font-size: 8pt")

        self.input_amt_label = QLabel("---")
        self.input_amt_label.setStyleSheet("font-weight: bold; color: green;")
        self.output_amt_label = QLabel("---")
        self.output_amt_label.setStyleSheet("font-weight: bold; color: orange;")
        self.remainder_label = QLabel("---")
        self.remainder_label.setStyleSheet("font-weight: bold;")

        self.sign_btn = QPushButton(QIcon("src\\dsc\\client\\ui\\assets\\icons\\key.png"), " Sign and Send")
        self.sign_btn.setMinimumSize(200, 50)
        self.sign_btn.setStyleSheet(styleSheets.big_btn + styleSheets.good_btn)
        self.sign_btn.setIconSize(QSize(20, 20))
        
        #============================================Layouts============================================
        wallet_layout = QHBoxLayout()
        wallet_layout.setContentsMargins(30, 20, 30, 20)
        wallet_layout.setSpacing(20)
        wallet_layout_container1 = QVBoxLayout()

        #---------Transaction List START---------
        tx_viewer = QVBoxLayout()
        tx_viewer.setSpacing(10)
        header1 = QHBoxLayout()
        header1.addWidget(self.output_tx_label)
        header1.addStretch()
        header1.addWidget(self.del_tx_btn)

        tx_viewer.addLayout(header1)
        tx_viewer.addWidget(self.output_tx_list)

        wallet_layout_container1.addLayout(tx_viewer, 2)

        #---------Transaction List END---------

        #---------Transaction Form START---------
        tx_form = QFormLayout()
        tx_form.setSpacing(10)
        tx_form.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.create_tx_label)
        header2 = QHBoxLayout()
        header2.addWidget(self.tx_name_field)
        header2.addWidget(QLabel("(optional)"))
        header2.addStretch()
        header2.addWidget(self.remainder_btn)
        tx_form.insertRow(1, "Tx Name:", header2)
        tx_form.insertRow(2, "Recipient:", self.pk2_field)

        amt_container = QHBoxLayout()
        amt_container.addWidget(self.amt_field)
        amt_container.addWidget(QLabel("DsCoins"))

        tx_form.insertRow(3, "Amount:", amt_container)
        
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.add_btn)
        btn_container.addWidget(self.clear_btn)

        tx_form.setLayout(4, QFormLayout.ItemRole.FieldRole, btn_container)
        tx_form.addRow(self.error_label)

        wallet_layout_container1.addLayout(tx_form, 1)

        #---------Transaction Form END---------

        wallet_layout_container2 = QVBoxLayout()
        wallet_layout_container2.setSpacing(10)

        #---------UTXO List START---------
        header3 = QHBoxLayout()
        header3.addWidget(self.input_tx_label)
        header3.addStretch()
        header3.addWidget(self.refresh_btn)
        header3.addWidget(self.select_all_btn)

        wallet_layout_container2.addLayout(header3)
        wallet_layout_container2.addWidget(self.input_tx_list)

        footer1 = QHBoxLayout()
        tx_data = QGridLayout()
        tx_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tx_data.addWidget(QLabel("Input Total (DSC):"), 0, 0)
        tx_data.addWidget(QLabel("Output Total (DSC):"), 1, 0)
        tx_data.addWidget(QLabel("Remainder (DSC):"), 2, 0)
        tx_data.addWidget(self.input_amt_label, 0, 1)
        tx_data.addWidget(self.output_amt_label, 1, 1)
        tx_data.addWidget(self.remainder_label, 2, 1)
        footer1.addLayout(tx_data)
        footer1.addStretch()
        footer1.addWidget(self.sign_btn)

        wallet_layout_container2.addLayout(footer1)

        #---------UTXO List END---------

        wallet_layout.addLayout(wallet_layout_container1)
        wallet_layout.addLayout(wallet_layout_container2)
        self.wallet_tab.setLayout(wallet_layout)
        
    def init_mine_tab(self):
        pass

    def init_menu(self):
        self.change_wallet_btn = QPushButton(QIcon().fromTheme("user-available"), "")
        self.change_wallet_btn.setToolTip("Change Wallets")
        self.change_wallet_btn.setStyleSheet("border: None;")
        self.switch_node_btn = QPushButton(QIcon().fromTheme("applications-internet"), "")
        self.switch_node_btn.setToolTip("Switch Nodes")
        self.switch_node_btn.setStyleSheet("border: None;")
        logo = QLabel("DsCoin Client")
        logo.setStyleSheet(styleSheets.header1)
        self.qotd = QLabel("My wallet is like an onion—opening it makes me cry.")
        self.qotd.setAlignment(Qt.AlignmentFlag.AlignBottom)
        menu_layout = QHBoxLayout()
        menu_layout.addWidget(logo)
        menu_layout.addWidget(self.qotd)
        menu_layout.addStretch()
        # menu_layout.addWidget(QLabel("Change Wallet"))
        menu_layout.addWidget(self.change_wallet_btn)
        menu_layout.addWidget(self.switch_node_btn)
        self.menu.setLayout(menu_layout)
        self.menu.setObjectName("menu")
        self.menu.setStyleSheet("QWidget#menu { background-color: #173F5F ;}")
       

class styleSheets:
    big_btn = "QPushButton {font-size: 12pt; font-weight: bold; padding: 10px;}"
    good_btn = "QPushButton:hover{background-color: green; color: white;} QPushButton:pressed{background-color: darkgreen}" 
    bad_btn = "QPushButton:hover{background-color: crimson; color: white;} QPushButton:pressed{background-color: darkred}"
    header1 = "QLabel{font-size: 18pt; font-weight: bold;}"
    header2 = "QLabel{font-size: 16pt; font-weight: bold;}"
    header3 = "QLabel{font-size: 12pt; font-weight: bold;}"

if __name__ in "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    win = DsCoinUI()
    win.show()
    app.exec()