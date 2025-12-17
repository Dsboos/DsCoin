from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QTextEdit, QPlainTextEdit,
QLineEdit, QPushButton, QTableWidget, QHBoxLayout, QLayout,
QVBoxLayout, QGridLayout, QTabBar, QFormLayout, QSpacerItem,
QTabWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSizePolicy, 
QMessageBox, QDoubleSpinBox, QStyle)
from PySide6.QtCore import Qt, QLocale, QSize
from PySide6.QtGui import QDoubleValidator, QIcon

class DsCoinUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DsCoin")
        self.resize(1080, 720)
        self.setMinimumSize(920, 600)

        #All elements
        self.output_tx_label = QLabel("Output Transactions")
        self.output_tx_label.setStyleSheet(styleSheets.header2)

        self.del_all_btn = QPushButton(QIcon.fromTheme("edit-delete"), " Delete All")
        self.del_all_btn.setMinimumWidth(100)
        self.del_all_btn.setStyleSheet(styleSheets.bad_btn)
        self.del_all_btn.setMaximumWidth(100)
        self.del_tx_btn = QPushButton("Delete")
        self.del_tx_btn.setStyleSheet(styleSheets.bad_btn)
        self.del_tx_btn.setMaximumWidth(100)

        self.output_tx_list = QTableWidget()
        self.output_tx_list.setColumnCount(4)
        self.output_tx_list.setHorizontalHeaderLabels(["Name", "Reciever Address", "Hash", "Amount (DSC)"])
        self.output_tx_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.output_tx_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.output_tx_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.output_tx_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.output_tx_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

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

        self.sk_field = QPlainTextEdit(placeholderText="Enter Private Key")
        self.sk_field.setMaximumHeight(50)

        self.error_label = QLabel("Test Error Test Error 1234 1234")
        self.error_label.setStyleSheet("color: crimson;")
        self.add_btn = QPushButton("Add")
        self.add_btn.setStyleSheet(styleSheets.good_btn)
        self.clear_btn = QPushButton("Clear All")

        self.input_tx_label = QLabel("Input Transactions")
        self.input_tx_label.setStyleSheet(styleSheets.header2)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMaximumWidth(100)
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon.fromTheme("system-reboot"))

        self.input_tx_list = QTableWidget()
        self.input_tx_list.setColumnCount(4)
        self.input_tx_list.setHorizontalHeaderLabels(["Hash", "Sender Address", "Amount (DSC)", "Select"])
        self.input_tx_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.input_tx_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.input_tx_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.input_tx_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.input_tx_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.input_amt_label = QLabel("---")
        self.input_amt_label.setStyleSheet("font-weight: bold; color: green;")
        self.output_amt_label = QLabel("---")
        self.output_amt_label.setStyleSheet("font-weight: bold; color: crimson;")
        self.remainder_label = QLabel("---")
        self.remainder_label.setStyleSheet("font-weight: bold;")

        self.sign_btn = QPushButton(QIcon("src\\dsc\\ui\\assets\\icons\\key.png"), " Sign Transaction")
        self.sign_btn.setStyleSheet(styleSheets.big_btn + styleSheets.good_btn)
        self.sign_btn.setIconSize(QSize(20, 20))
        
        self.initUI()

    def initUI(self):
        master_layout = QGridLayout()
        
        #---------------Transaction Wizard START---------------
        tx_wizard = QGroupBox("Transactions")
        tx_layout = QHBoxLayout()
        tx_layout.setContentsMargins(40, 20, 40, 20)
        tx_layout.setSpacing(20)
        tx_layout_container1 = QVBoxLayout()

        #---------Transaction List START---------
        tx_viewer = QVBoxLayout()
        tx_viewer.setSpacing(10)
        header1 = QHBoxLayout()
        header1.addWidget(self.output_tx_label)
        header1.addStretch()
        header1.addWidget(self.del_tx_btn)
        header1.addWidget(self.del_all_btn)

        tx_viewer.addLayout(header1)
        tx_viewer.addWidget(self.output_tx_list)

        tx_layout_container1.addLayout(tx_viewer, 2)

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

        tx_layout_container1.addLayout(tx_form, 1)

        #---------Transaction Form END---------

        tx_layout_container2 = QVBoxLayout()
        tx_layout_container2.setSpacing(10)

        #---------UTXO List START---------
        header3 = QHBoxLayout()
        header3.addWidget(self.input_tx_label)
        header3.addStretch()
        header3.addWidget(self.select_all_btn)
        header3.addWidget(self.refresh_btn)

        tx_layout_container2.addLayout(header3)
        tx_layout_container2.addWidget(self.input_tx_list)

        sk_container = QHBoxLayout()
        sk_label = QLabel("Private Key:")
        sk_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        sk_container.addWidget(sk_label)
        sk_container.addWidget(self.sk_field)

        tx_layout_container2.addLayout(sk_container)
        tx_layout_container2.addSpacerItem(QSpacerItem(0, 20))

        footer1 = QHBoxLayout()
        tx_data = QGridLayout()
        tx_data.addWidget(QLabel("Tx Input Total:"), 0, 0)
        tx_data.addWidget(QLabel("Tx Output Total:"), 1, 0)
        tx_data.addWidget(QLabel("Remainder:"), 2, 0)
        tx_data.addWidget(self.input_amt_label, 0, 1)
        tx_data.addWidget(self.output_amt_label, 1, 1)
        tx_data.addWidget(self.remainder_label, 2, 1)
        footer1.addLayout(tx_data)
        footer1.addWidget(self.sign_btn)

        tx_layout_container2.addLayout(footer1)

        #---------UTXO List END---------

        tx_layout.addLayout(tx_layout_container1)
        tx_layout.addLayout(tx_layout_container2)
        tx_wizard.setLayout(tx_layout)
        master_layout.addWidget(tx_wizard, 0, 0)

        #---------------Transaction Wizard END---------------

        self.setLayout(master_layout)
        
class styleSheets:
    big_btn = "QPushButton {font-size: 12pt; font-weight: bold; padding: 10px;}"
    good_btn = "QPushButton:hover{background-color: green; color: white;} QPushButton:pressed{background-color: darkgreen}" 
    bad_btn = "QPushButton:hover{background-color: crimson; color: white;} QPushButton:pressed{background-color: darkred}"
    header1 = "QLabel{font-size: 18pt; font-weight: bold;}"
    header2 = "QLabel{font-size: 16pt; font-weight: bold;}"
    header3 = "QLabel{font-size: 12pt; font-weight: bold;}"

if __name__ in "__main__":
    app = QApplication()
    win = DsCoinUI()
    win.show()
    app.exec()