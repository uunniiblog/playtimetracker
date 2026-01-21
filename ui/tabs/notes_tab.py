import config
from core.log_manager import LogManager
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QTextEdit, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

class NotesTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.log_manager = LogManager(config.LOG_DIR)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        controls = QHBoxLayout()
        self.app_combo = QComboBox()
        self.app_combo.currentIndexChanged.connect(self.load_note)
        controls.addWidget(self.app_combo)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self.refresh_list)
        controls.addWidget(refresh_btn)
        layout.addLayout(controls)

        self.editor = QTextEdit()
        layout.addWidget(self.editor)

        self.save_btn = QPushButton("Save Note")
        self.save_btn.clicked.connect(self.save_note)
        layout.addWidget(self.save_btn)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        self.status.setVisible(False)
        layout.addWidget(self.status)

        self.refresh_list()

    def refresh_list(self):
        self.app_combo.clear()
        logs = self.log_manager.get_apps_sorted_by_latest()
        self.app_combo.addItems(logs)
        self.app_combo.blockSignals(False)
        self.load_note()

    def load_note(self):
        app = self.app_combo.currentText()
        process = self.log_manager._extract_process(app)
        content = self.data.get_note(process)
        self.editor.setPlainText(content)
        self.status.setVisible(False)

    def save_note(self):
        app = self.app_combo.currentText()
        process = self.log_manager._extract_process(app)
        if app:
            self.data.save_note(process, self.editor.toPlainText())

            self.status.setText(f"✓ Note saved for {process}")
            self.status.setVisible(True)

            self.save_btn.setText("Saved!")
            self.save_btn.setEnabled(False)

            QTimer.singleShot(3000, self.reset_feedback)

    def reset_feedback(self):
        self.status.setVisible(False)
        self.save_btn.setText("Save Note")
        self.save_btn.setEnabled(True)
