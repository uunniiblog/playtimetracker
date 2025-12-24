from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer
import config

class SettingsTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(f"PlayTimeTracker {config.VERSION}\n{config.GIT_URL}")
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info)

        self.editor = QTextEdit()
        if config.SETTINGS_FILE.exists():
            self.editor.setPlainText(config.SETTINGS_FILE.read_text())

        self.editor.textChanged.connect(lambda: self.status.setVisible(False))
        layout.addWidget(self.editor)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        self.status.setVisible(False)
        layout.addWidget(self.status)

    def save(self):
        self.data.save_settings_text(self.editor.toPlainText())

        self.status.setText("✓ Settings applied successfully")
        self.status.setVisible(True)

        self.save_btn.setText("Saved!")
        self.save_btn.setEnabled(False)

        QTimer.singleShot(3000, self.reset_feedback)

    def reset_feedback(self):
        self.status.setVisible(False)
        self.save_btn.setText("Save Settings")
        self.save_btn.setEnabled(True)
