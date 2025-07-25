from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFormLayout, QLineEdit, QMessageBox, QWidget, QScrollArea
)
from PyQt5.QtGui import QFont, QIntValidator, QPalette, QColor
from PyQt5.QtCore import Qt

class ObjectToBayDialog(QDialog):
    def __init__(self, object_names, num_bays=16, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assign Objects to Bays")
        self.setMinimumSize(600, 500)
        self.object_names = object_names
        self.num_bays = num_bays
        self.assignments = {}

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(18)

        title = QLabel("Assign Each Object to a Bay")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #000000; background: #ffffff; margin-bottom: 18px; border-radius: 8px; padding: 8px;")
        main_layout.addWidget(title)

        # Scroll area for many objects
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form = QFormLayout(scroll_content)
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        form.setSpacing(14)
        self.edits = {}

        int_validator = QIntValidator(1, num_bays, self)
        for obj in object_names:
            edit = QLineEdit(self)
            font = QFont("Segoe UI", 14)
            edit.setFont(font)
            edit.setValidator(int_validator)
            edit.setPlaceholderText(f"Enter bay (1-{num_bays})")
            edit.setFixedWidth(120)
            edit.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #bc85fa;
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 16px;
                    background: #ffffff;
                    color: #000000;
                }
                QLineEdit:focus {
                    border: 2px solid #7E57C2;
                    background: #f5f5f5;
                    color: #000000;
                }
            """)
            edit.textChanged.connect(self.validate_all)
            self.edits[obj] = edit
            label = QLabel(obj)
            label.setFont(font)
            label.setStyleSheet("color: #000000; background: #ffffff; border-radius: 8px; padding: 4px 8px;")
            form.addRow(label, edit)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border-radius: 8px;
                padding: 10px 32px;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
                color: #eee;
            }
            QPushButton:hover:!disabled {
                background-color: #512da8;
            }
        """)
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        btn_layout.addWidget(self.ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 14))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e57373;
                color: white;
                border-radius: 8px;
                padding: 10px 32px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog {
                background: #f8f9fa;
            }
        """)

        self.validate_all()

    def validate_all(self):
        valid = True
        used_bays = set()
        for obj, edit in self.edits.items():
            text = edit.text()
            palette = edit.palette()
            if not text.isdigit() or not (1 <= int(text) <= self.num_bays):
                palette.setColor(QPalette.Base, QColor("#ffcccc"))
                valid = False
            elif int(text) in used_bays:
                palette.setColor(QPalette.Base, QColor("#ffe082"))  # yellow for duplicate
                valid = False
            else:
                palette.setColor(QPalette.Base, QColor("#f3eaff"))
                used_bays.add(int(text))
            edit.setPalette(palette)
        self.ok_btn.setEnabled(valid)

    def get_assignments(self):
        # Returns a dict: {object_name: bay_number (int)}
        return {obj: int(edit.text()) for obj, edit in self.edits.items()}