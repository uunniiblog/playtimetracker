import config
from core.log_manager import LogManager
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QLabel, QScrollArea, QMenu
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, Qt
from pathlib import Path

class LogsTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.log_manager = LogManager(config.LOG_DIR)
        self.tables = [] 
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # --- Top Controls ---
        top_bar = QHBoxLayout()
        self.app_combo = QComboBox()
        self.app_combo.currentIndexChanged.connect(self.load_log)
        top_bar.addWidget(self.app_combo, 1)
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_list)
        top_bar.addWidget(refresh_btn)
        self.main_layout.addLayout(top_bar)

        # --- Scroll Area ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        # --- Bottom Buttons ---
        btn_layout = QHBoxLayout()
        
        self.status = QLabel("")
        self.status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        btn_layout.addWidget(self.status)
        
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save All Changes")
        self.save_btn.clicked.connect(self.save_all)
        self.save_btn.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        btn_layout.addWidget(self.save_btn)
        
        self.main_layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        """Uses LogManager to get the latest updated apps."""
        current = self.app_combo.currentText()
        self.app_combo.blockSignals(True)
        self.app_combo.clear()
        
        # Get apps from the JSON metadata cache
        apps = self.log_manager.get_apps_sorted_by_latest()
        self.app_combo.addItems(apps)
        
        if current in apps:
            self.app_combo.setCurrentText(current)
            
        self.app_combo.blockSignals(False)
        self.load_log()

    def load_log(self):
        app = self.app_combo.currentText()
        
        # Clear existing table widgets
        for i in reversed(range(self.container_layout.count())): 
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.tables = []
        if not app: return

        grouped_logs = self.log_manager.get_grouped_logs_for_app(app)
        headers = self.log_manager.header.strip().split(";")

        if not grouped_logs:
            self.container_layout.addWidget(QLabel("No logs found for this application."))
            return

        for date_str, rows in grouped_logs.items():
            date_label = QLabel(f"📅 {date_str}")
            date_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 15px; color: #3498db;")
            self.container_layout.addWidget(date_label)

            table = QTableWidget(len(rows), len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setProperty("date_source", date_str) 
            
            for r, row_data in enumerate(rows):
                for c, text in enumerate(row_data):
                    table.setItem(r, c, QTableWidgetItem(text))
            
            # --- FIXED SCROLL & HEIGHT LOGIC ---
            
            # Use Qt.ScrollBarPolicy instead of QAbstractItemView
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # Improved height calculation
            # Row height (30) * num rows + Header (35) + Scrollbar space (25)
            row_count = table.rowCount()
            calculated_height = (row_count * 30) + 65
            
            # Ensure 1-row entries aren't squashed (min 110), limit max to 400
            final_height = max(110, min(400, calculated_height))
            table.setFixedHeight(final_height)
            
            # Set a standard row height for consistency
            table.verticalHeader().setDefaultSectionSize(30)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

            # Enable right click
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(lambda pos, t=table: self.show_context_menu(pos, t))

            self.container_layout.addWidget(table)
            self.tables.append(table)

        self.container_layout.addStretch()

    def save_all(self):
        """Iterates through all visible tables and updates each daily CSV."""
        app_name = self.app_combo.currentText()
        if not app_name: return

        try:
            for table in self.tables:
                date_str = table.property("date_source")
                
                # Extract data from UI table
                new_app_rows = []
                for r in range(table.rowCount()):
                    row_data = []
                    for c in range(table.columnCount()):
                        item = table.item(r, c)
                        row_data.append(item.text() if item else "")
                    new_app_rows.append(";".join(row_data))

                # Update the file
                self.update_daily_file(date_str, app_name, new_app_rows)

            self.status.setText("✓ All files updated")
            self.status.setVisible(True)
            QTimer.singleShot(3000, lambda: self.status.setVisible(False))
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")

    def update_daily_file(self, date_str, combined_name, new_app_rows):
        """Helper to overwrite only specific app entries."""
        app_process = self.log_manager._extract_process(combined_name)
        
        year_month = date_str[:7]
        file_path = self.log_manager.log_dir / year_month / f"activity_{date_str}.csv"
        
        if not file_path.exists(): return

        lines = file_path.read_text(encoding="utf-8").splitlines()
        header = lines[0]
        
        # Keep rows belonging to OTHER apps by comparing with app_process
        other_apps_data = [
            line for line in lines[1:] 
            if line.strip() and line.split(";")[4] != app_process
        ]
        
        final_lines = [header] + other_apps_data + new_app_rows
        file_path.write_text("\n".join(final_lines) + "\n", encoding="utf-8")

    def show_context_menu(self, pos, table):
        """Displays a menu when right-clicking a row."""
        menu = QMenu()
        delete_action = QAction("🗑 Delete Selected Row(s)", self)
        delete_action.triggered.connect(lambda: self.delete_selected_rows(table))
        menu.addAction(delete_action)
        menu.exec(table.mapToGlobal(pos))

    def delete_selected_rows(self, table):
        """Removes rows from the table and shrinks the table height."""
        # Get selected unique row indices in reverse order
        selected_items = table.selectedItems()
        if not selected_items:
            return

        rows_to_delete = sorted(list(set(item.row() for item in selected_items)), reverse=True)

        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to remove {len(rows_to_delete)} entry(s)?\n\nNote: Changes are only permanent after clicking 'Save All Changes'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            for row in rows_to_delete:
                table.removeRow(row)
            
            # Re-calculate height so the UI shrinks nicely
            new_row_count = table.rowCount()
            if new_row_count == 0:
                # If no rows left for this day, we could hide the table or just make it small
                table.setFixedHeight(65) 
            else:
                new_height = max(110, min(400, (new_row_count * 30) + 65))
                table.setFixedHeight(new_height)