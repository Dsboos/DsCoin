from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QTextEdit, QPlainTextEdit,
                               QLineEdit, QPushButton, QTableWidget, QHBoxLayout, QLayout,
                               QVBoxLayout, QGridLayout, QTabBar, QFormLayout, QSpacerItem,
                               QTabWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSizePolicy, 
                               QMessageBox, QDoubleSpinBox, QStyle, QMainWindow, QAbstractItemView,
                               QSpinBox, QDialog, QComboBox)
from PySide6.QtCore import Qt, QLocale, QSize
from PySide6.QtGui import QDoubleValidator, QIcon, QAction
import qdarktheme
import sys

class DsCoinUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DsCoin Client v0.1.0")
        self.setWindowIcon(QIcon("src\\dsc\\client\\ui\\assets\\icons\\logo.png"))
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
        self.init_mine_tab()
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
        #============================================UI Elements============================================
        self.preview_box = QGroupBox("Block Preview")
        self.preview_label = QLabel("Block Preview")
        self.preview_label.setStyleSheet(styleSheets.header2)

        self.block_name = QLabel("---")
        self.block_name.setStyleSheet("font-weight: bold;")
        self.block_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.block_nonce = QLabel("---")
        self.block_nonce.setStyleSheet("font-weight: bold;")
        self.block_diff = QLabel("---")
        self.block_diff.setStyleSheet("font-weight: bold;")
        self.block_limit = QLabel("---")
        self.block_limit.setStyleSheet("font-weight: bold;")
        self.block_prev = QLabel("---")
        self.block_prev.setStyleSheet("font-weight: bold;")
        self.block_reward = QLabel("---")
        self.block_reward.setStyleSheet("font-weight: bold;")
        self.block_mine_status = QLabel("---")
        self.block_mine_status.setStyleSheet("font-weight: bold;")

        self.block_tx_list = QPlainTextEdit()
        self.block_tx_list.setReadOnly(True)
        self.block_cbtx_list = QPlainTextEdit()
        self.block_cbtx_list.setReadOnly(True)

        self.create_block_btn = QPushButton("Create Block")
        self.create_block_btn.setStyleSheet(styleSheets.good_btn)
        self.del_block_btn = QPushButton("Delete Block")
        self.del_block_btn.setStyleSheet(styleSheets.bad_btn)
        self.edit_block_btn = QPushButton("Edit Details")

        self.mempool_label = QLabel("Mempool")
        self.mempool_label.setStyleSheet(styleSheets.header2)

        self.select_limit_btn = QPushButton("Select Limit")
        self.select_limit_btn.setMaximumWidth(100)
        self.refresh_mempool_btn = QPushButton()
        self.refresh_mempool_btn.setIcon(QIcon.fromTheme("system-reboot"))

        self.mempool_list = QTableWidget()
        self.mempool_list.setColumnCount(3)
        self.mempool_list.verticalHeader().setVisible(False)
        self.mempool_list.setHorizontalHeaderLabels(["Hash", "Fee\n(DSC)", "Select"])
        self.mempool_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mempool_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.mempool_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.mempool_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.mempool_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mempool_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.mempool_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.mempool_list.setStyleSheet("font-size: 8pt")

        self.mine_error_label = QLabel("Test Error Test Error 1234 1234")
        self.mine_error_label.setStyleSheet("color: crimson;")

        self.cb_label = QLabel("Add Coin Base")
        self.cb_label.setStyleSheet(styleSheets.header2)

        self.cb_name_field = QLineEdit(placeholderText="Enter Name")
        self.cb_name_field.setMaxLength(18)
        self.cb_name_field.setFixedWidth(180)
        self.cb_pk_field = QPlainTextEdit(placeholderText="Enter Reciever Key")
        self.cb_pk_field.setMaximumHeight(50)
        self.cb_amt_field = QDoubleSpinBox()
        self.cb_amt_field.setRange(0.0, 1000000.0)
        self.cb_amt_field.setDecimals(4)
        self.cb_amt_field.setMaximumWidth(150)
        self.cb_password_field = QLineEdit(placeholderText="Enter Password")
        self.cb_password_field.setMaximumWidth(450)

        self.add_cb_btn = QPushButton("Add Coins")
        self.add_cb_btn.setStyleSheet(styleSheets.good_btn)
        self.add_cb_btn.setMaximumWidth(100)

        self.mine_label = QLabel("Mine Block")
        self.mine_label.setStyleSheet(styleSheets.header2)

        self.seq_field = QLineEdit()
        self.seq_field.setMaximumWidth(150)
        self.seq_field.setReadOnly(True)

        self.hash_field = QLineEdit()
        self.hash_field.setMinimumWidth(450)
        self.hash_field.setReadOnly(True)
        
        self.mine_btn = QPushButton("Mine Block")
        self.mine_btn.setStyleSheet(styleSheets.good_btn)
        self.mine_btn.setMaximumWidth(100)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(styleSheets.bad_btn)
        self.cancel_btn.setMaximumWidth(100)
        self.cancel_btn.hide()

        self.submit_btn = QPushButton("Submit Block")
        self.submit_btn.setFixedSize(200, 50)
        self.submit_btn.setStyleSheet(styleSheets.big_btn + styleSheets.good_btn)
        self.submit_btn.setIconSize(QSize(20, 20))

        self.mine_preset_menu = QComboBox()
        self.mine_preset_menu.addItems(["Potato", "Low", "Medium", "High", "Ultra"])
        self.mine_preset_menu.setCurrentIndex(2)
        self.mine_preset_menu.setPlaceholderText("Select Preset")

        #============================================Layouts============================================
        mine_layout = QHBoxLayout()
        mine_layout.setContentsMargins(30, 20, 30, 20)
        mine_layout.setSpacing(20)

        mine_layout_container1 = QVBoxLayout()
        mine_layout_container1.setSpacing(10)

        #---------Coin Base Form START---------
        cb_form = QFormLayout()
        cb_form.setSpacing(10)
        cb_form.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.cb_label)
        header2 = QHBoxLayout()
        header2.addWidget(self.cb_name_field)
        header2.addWidget(QLabel("(optional)"))
        cb_form.insertRow(1, "Tx Name:", header2)

        amt_container = QHBoxLayout()
        amt_container.addWidget(self.cb_amt_field)
        amt_container.addWidget(QLabel("DsCoins"))

        cb_form.insertRow(2, "Amount:", amt_container)
        cb_form.insertRow(3, "Reciever's Key:", self.cb_pk_field)
        cb_form.insertRow(4, "Password:", self.cb_password_field)
        cb_form.setWidget(5, QFormLayout.ItemRole.FieldRole, self.add_cb_btn)
        #---------Coin Base Form END---------

        mine_layout_container1.addLayout(cb_form, 1)

        #---------Mempool Selection START---------
        header1 = QHBoxLayout()
        header1.addWidget(self.mempool_label)
        header1.addStretch()
        header1.addWidget(self.refresh_mempool_btn)
        header1.addWidget(self.select_limit_btn)

        mine_layout_container1.addLayout(header1)
        mine_layout_container1.addWidget(self.mempool_list, 2)
        mine_layout_container1.addWidget(self.mine_error_label)
        #---------Mempool Selection END---------
        
        mine_layout_container2 = QVBoxLayout()
        mine_layout_container2.setSpacing(10)

        #---------Block Preview START---------
        groupbox_container = QVBoxLayout()
        groupbox_container.setContentsMargins(20, 10, 20, 10)

        header_container = QHBoxLayout()
        block_header = QLabel("Header:")
        block_header.setStyleSheet(styleSheets.header3)
        header_container.addWidget(block_header)
        header_container.addStretch()
        header_container.addWidget(self.create_block_btn)

        groupbox_container.addLayout(header_container)
        groupbox_container.addSpacing(10)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Block Name:"))
        row1.addWidget(self.block_name)
        row1.addStretch()
        row1.addWidget(QLabel("Nonce:"))
        row1.addWidget(self.block_nonce)
        row1.addStretch() 
        groupbox_container.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Previous Block:"))
        row2.addWidget(self.block_prev)
        row2.addStretch()
        groupbox_container.addLayout(row2)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Difficulty:"))
        row3.addWidget(self.block_diff)
        row3.addStretch()
        row3.addWidget(QLabel("Reward:"))
        row3.addWidget(self.block_reward)
        row3.addStretch()
        row3.addWidget(QLabel("Tx Limit:"))
        row3.addWidget(self.block_limit)
        row3.addStretch()
        groupbox_container.addLayout(row3)
        groupbox_container.addSpacing(10)

        block_body = QLabel("Body:")
        block_body.setStyleSheet(styleSheets.header3)
        groupbox_container.addWidget(block_body)

        groupbox_container.addWidget(QLabel("Tx:"))
        groupbox_container.addWidget(self.block_tx_list)
        groupbox_container.addWidget(QLabel("CBTx:"))
        groupbox_container.addWidget(self.block_cbtx_list)

        hash_container = QHBoxLayout()
        hash_container.addWidget(QLabel("Block Hash:"))
        hash_container.addWidget(self.hash_field)
        hash_container.addStretch()
        groupbox_container.addLayout(hash_container)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Mine Sequence:"))
        row4.addWidget(self.seq_field)
        row4.addStretch()

        groupbox_container.addLayout(row4)
        groupbox_container.addSpacing(20)

        create_container = QHBoxLayout()
        create_container.addWidget(self.del_block_btn)
        create_container.addStretch()
        create_container.addWidget(self.mine_btn)
        create_container.addWidget(self.cancel_btn)
        groupbox_container.addLayout(create_container)

        self.preview_box.setLayout(groupbox_container)
        mine_layout_container2.addWidget(self.preview_box, 2)
        #---------Block Preview END---------
        
        submit_btn_container = QHBoxLayout()
        submit_btn_container.addWidget(QLabel("Mining Preset:"))
        submit_btn_container.addWidget(self.mine_preset_menu)
        submit_btn_container.addWidget(QLabel("Status:"))
        submit_btn_container.addWidget(self.block_mine_status)
        submit_btn_container.addStretch()
        submit_btn_container.addWidget(self.submit_btn)
        mine_layout_container2.addLayout(submit_btn_container)

        mine_layout.addLayout(mine_layout_container1, 1)
        mine_layout.addLayout(mine_layout_container2, 1)
        self.mine_tab.setLayout(mine_layout)

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


class CreateBlockUI(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle("Block Details")
        self.setWindowIcon(QIcon("src\\dsc\\client\\ui\\assets\\icons\\logo.png"))

    def initUI(self):
        self.details_label = QLabel("Block Details")
        self.details_label.setStyleSheet(styleSheets.header2)

        self.block_name_field = QLineEdit(placeholderText="Enter Name")
        self.block_name_field.setMaxLength(18)
        self.block_name_field.setFixedWidth(180)
        self.prev_field = QLineEdit(placeholderText="Enter Previous Hash")
        self.prev_field.setMaximumWidth(450)

        self.reward_field = QDoubleSpinBox()
        self.reward_field.setRange(0.0, 1000000.0)
        self.reward_field.setDecimals(4)
        self.reward_field.setValue(64.0)
        self.reward_field.setMaximumWidth(150)

        self.diff_field = QSpinBox()
        self.diff_field.setRange(0, 64)
        self.diff_field.setValue(3)
        self.diff_field.setMaximumWidth(150)
        
        self.limit_field = QSpinBox()
        self.limit_field.setRange(0, 16)
        self.limit_field.setValue(5)
        self.limit_field.setMaximumWidth(150)

        self.load_details_btn = QPushButton(QIcon.fromTheme("emblem-downloads"), "")
        self.load_details_btn.setMaximumWidth(100)
        self.load_details_btn.setAutoDefault(False)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet(styleSheets.good_btn)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(styleSheets.bad_btn)
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.clicked.connect(self.reject)

        #------------Layout-------------
        self.setContentsMargins(20, 10, 20, 10)
        main_layout = QVBoxLayout()

        details_form = QFormLayout()
        details_form.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(self.details_label)
        header.addStretch()
        header.addWidget(QLabel("Load Details from Node"))
        header.addWidget(self.load_details_btn)
        details_form.setLayout(0, QFormLayout.ItemRole.SpanningRole, header)

        header3 = QHBoxLayout()
        header3.addWidget(self.block_name_field)
        header3.addWidget(QLabel("(optional)"))
        header3.addStretch()
        header3.addWidget(QLabel("Tx Limit:"))
        header3.addWidget(self.limit_field)
        details_form.insertRow(1, "Block Name:", header3)
        
        details_form.insertRow(2, "Previous Block:", self.prev_field)

        reward_container = QHBoxLayout()
        reward_container.addWidget(self.reward_field)
        reward_container.addWidget(QLabel("DsCoins"))
        reward_container.addStretch()
        reward_container.addWidget(QLabel("Difficulty:"))
        reward_container.addWidget(self.diff_field)

        details_form.insertRow(3, "Reward:", reward_container)

        main_layout.addLayout(details_form)
        main_layout.addSpacing(20)
        btn_container = QHBoxLayout()
        btn_container.addWidget(self.cancel_btn)
        btn_container.addStretch()
        btn_container.addWidget(self.save_btn)
        main_layout.addLayout(btn_container)
        self.setLayout(main_layout)


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