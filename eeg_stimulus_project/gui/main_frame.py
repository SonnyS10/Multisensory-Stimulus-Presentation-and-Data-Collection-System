from PyQt5.QtWidgets import QFrame, QVBoxLayout, QStackedWidget

class MainFrame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget)