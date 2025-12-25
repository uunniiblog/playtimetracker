from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QLabel, QAbstractItemView
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

class LogsTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Top Bar (Selector & Refresh) ---
        top_layout = QHBoxLayout()
        
        self.app_combo = QComboBox()
        self.app_combo.currentIndexChanged.connect(self.load_log)
        top_layout.addWidget(self.app_combo, 1)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self.refresh_list)
        top_layout.addWidget(refresh_btn)
        
        layout.addLayout(top_layout)

        # --- Row Manipulation Controls ---
        row_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("Add New Entry")
        add_row_btn.clicked.connect(self.add_row)
        row_layout.addWidget(add_row_btn)

        del_row_btn = QPushButton("Delete Selected Entry")
        del_row_btn.clicked.connect(self.delete_row)
        row_layout.addWidget(del_row_btn)

        # Spacer to push the red button to the far right
        row_layout.addStretch()

        # Delete File Button (Red)
        self.del_file_btn = QPushButton("Delete Entire Log File")
        self.del_file_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.del_file_btn.clicked.connect(self.delete_entire_log)
        row_layout.addWidget(self.del_file_btn)

        layout.addLayout(row_layout)

        # --- The Table ---
        self.table = QTableWidget()
        # Resize logic: Interactive headers, last column stretches
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        # Allow selecting entire rows
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # --- Save Area ---
        save_layout = QHBoxLayout()
        
        self.status = QLabel("")
        self.status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        self.status.setVisible(False)
        save_layout.addWidget(self.status)
        
        save_layout.addStretch()

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_log)
        save_layout.addWidget(self.save_btn)

        layout.addLayout(save_layout)

        # Initial Load
        self.refresh_list()

    def refresh_list(self):
        current = self.app_combo.currentText()
        self.app_combo.blockSignals(True)
        self.app_combo.clear()
        
        logs = self.data.get_log_files()
        self.app_combo.addItems(logs.keys())
        
        # Restore selection if it still exists
        if current in logs:
            self.app_combo.setCurrentText(current)
            
        self.app_combo.blockSignals(False)
        
        # Trigger load if we have items, else clear table
        if self.app_combo.count() > 0:
            self.load_log()
        else:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.del_file_btn.setEnabled(False)
            self.save_btn.setEnabled(False)

    def load_log(self):
        app = self.app_combo.currentText()
        if not app: return

        self.del_file_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        headers, data = self.data.get_log_content(app)

        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, row_data in enumerate(data):
            for col_idx, text in enumerate(row_data):
                if col_idx < len(headers):
                    item = QTableWidgetItem(str(text))
                    self.table.setItem(row_idx, col_idx, item)

        self.status.setVisible(False)

    def add_row(self):
        """Adds an empty row at the bottom of the table."""
        if self.table.columnCount() == 0:
            QMessageBox.warning(self, "Error", "No log loaded to add rows to.")
            return
            
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        for c in range(self.table.columnCount()):
            self.table.setItem(row_count, c, QTableWidgetItem(""))

    def delete_row(self):
        """Deletes the currently selected row(s)."""
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        
        if not rows:
            QMessageBox.warning(self, "Selection Error", "Please select a row to delete.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete {len(rows)} entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            for r in rows:
                self.table.removeRow(r)

    def delete_entire_log(self):
        """Deletes the physical file and refreshes the list."""
        app = self.app_combo.currentText()
        if not app: return

        confirm = QMessageBox.warning(
            self, "Delete Log File", 
            f"Are you sure you want to PERMANENTLY delete the log file for:\n\n{app}\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.data.delete_log_file(app)
            if success:
                self.status.setText(f"File deleted: {app}")
                self.status.setVisible(True)
                self.refresh_list()
            else:
                QMessageBox.critical(self, "Error", "Could not delete file.")

    def save_log(self):
        app = self.app_combo.currentText()
        if not app: return

        # Scrape Headers
        headers = []
        for c in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(c)
            headers.append(item.text() if item else "")

        # Scrape Data
        data = []
        for r in range(self.table.rowCount()):
            row_items = []
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                row_items.append(item.text() if item else "")
            data.append(row_items)

        # Save via DataManager
        success = self.data.save_log_content(app, headers, data)

        if success:
            self.status.setText(f"✓ Log updated for {app}")
            self.status.setVisible(True)
            self.save_btn.setText("Saved!")
            self.save_btn.setEnabled(False)
            QTimer.singleShot(2000, self.reset_feedback)
        else:
            QMessageBox.critical(self, "Error", "Failed to save log file!")

    def reset_feedback(self):
        self.status.setVisible(False)
        self.save_btn.setText("Save Changes")
        self.save_btn.setEnabled(True)