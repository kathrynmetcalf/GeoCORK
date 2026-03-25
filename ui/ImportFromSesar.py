#This should open a blank box for now. 
# I will add comments later
# ImportFromSesar.py
from PyQt6.QtCore import Qt  
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class ImportFromSesar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from Sesar")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        label = QLabel("Import from Sesar Coming Soon :D")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        layout.addWidget(label)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)