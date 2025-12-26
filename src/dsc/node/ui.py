from PySide6.QtWidgets import (QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QApplication)
from PySide6.QtCore import Qt
from pyqtgraph.console import ConsoleWidget
import qdarktheme
import sys

class NodeUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.console = ConsoleWidget()
        self.setCentralWidget(self.console)

if __name__ in "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    win = NodeUI()
    win.show()
    
    app.exec()
