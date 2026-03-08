import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import database
import add_edit_dialog
import alerts_dialog
import helpers
from psycopg2 import extras
from datetime import date, timedelta

class AnimatedButton(QtWidgets.QPushButton):
    """A button with a smooth background color animation on hover."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.default_stylesheet = """
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
            }
        """
        self.hover_stylesheet = """
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #777;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
            }
        """
        self.setStyleSheet(self.default_stylesheet)

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_stylesheet)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_stylesheet)
        super().leaveEvent(event)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventario de Farmacia")
        self.setGeometry(100, 100, 1300, 700)
        self.setStyleSheet(self.load_stylesheet())

        # Central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Toolbar
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.edit_medication)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #3c3c3c;
                gridline-color: transparent;
                selection-background-color: #4a6b8a;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.table)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e;
                color: #ccc;
            }
        """)
        self.update_status_bar()

        # Set headers
        self.headers = ['ID', 'Nombre', 'Código', 'Lote', 'Vencimiento', 'Precio', 'Cantidad', 'Categoría']
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.hideColumn(0)

        self.load_data()
        self.check_alerts_and_notify()

    def create_toolbar(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(10)

        # Search
        search_label = QtWidgets.QLabel("🔍 Buscar:")
        search_label.setStyleSheet("font-size: 10pt; padding: 5px;")
        layout.addWidget(search_label)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Nombre o código...")
        self.search_edit.setFixedHeight(30)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                font-size: 10pt;
            }
        """)
        self.search_edit.textChanged.connect(self.load_data)
        layout.addWidget(self.search_edit, 1)  # stretch factor

        # Spacer
        layout.addStretch(2)

        # Buttons (using AnimatedButton)
        self.add_btn = AnimatedButton("➕ Agregar")
        self.add_btn.clicked.connect(self.add_medication)
        layout.addWidget(self.add_btn)

        self.edit_btn = AnimatedButton("✏️ Editar")
        self.edit_btn.clicked.connect(self.edit_medication)
        layout.addWidget(self.edit_btn)

        self.delete_btn = AnimatedButton("🗑️ Eliminar")
        self.delete_btn.clicked.connect(self.delete_medication)
        layout.addWidget(self.delete_btn)

        self.alerts_btn = AnimatedButton("⚠️ Alertas")
        self.alerts_btn.clicked.connect(self.show_alerts)
        layout.addWidget(self.alerts_btn)

        self.export_btn = AnimatedButton("📤 Exportar CSV")
        self.export_btn.clicked.connect(self.export_csv)
        layout.addWidget(self.export_btn)

        return layout

    def load_stylesheet(self):
        return """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 10pt;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #7a8a9a;
            }
            QTableWidget {
                border: none;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
            QScrollBar:horizontal {
                background: #2b2b2b;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #555;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #777;
            }
        """

    def load_data(self):
        search = self.search_edit.text().strip()
        conn = database.get_connection()
        if not conn:
            QtWidgets.QMessageBox.critical(self, "Error", "No se pudo conectar a la base de datos.")
            return
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                if search:
                    cur.execute("""
                        SELECT m.id, m.name, m.code, m.lot, m.expiration_date,
                               m.price, m.quantity, c.name as category
                        FROM medications m
                        LEFT JOIN categories c ON m.category_id = c.id
                        WHERE m.name ILIKE %s OR m.code ILIKE %s
                        ORDER BY m.name
                    """, (f'%{search}%', f'%{search}%'))
                else:
                    cur.execute("""
                        SELECT m.id, m.name, m.code, m.lot, m.expiration_date,
                               m.price, m.quantity, c.name as category
                        FROM medications m
                        LEFT JOIN categories c ON m.category_id = c.id
                        ORDER BY m.name
                    """)
                rows = cur.fetchall()
                self.table.setRowCount(len(rows))
                today = date.today()
                for i, row in enumerate(rows):
                    # Determine background color based on conditions
                    bg_color = None
                    if row['quantity'] < 5:
                        bg_color = QtGui.QColor(200, 70, 70)  # red
                    elif row['expiration_date'] <= today + timedelta(days=30):
                        bg_color = QtGui.QColor(200, 130, 50)  # orange

                    # Set items
                    self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row['id'])))
                    self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(row['name']))
                    self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(row['code']))
                    self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(row['lot'] or ''))
                    self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(row['expiration_date'].strftime('%Y-%m-%d')))
                    self.table.setItem(i, 5, QtWidgets.QTableWidgetItem(f"{row['price']:.2f}"))
                    self.table.setItem(i, 6, QtWidgets.QTableWidgetItem(str(row['quantity'])))
                    self.table.setItem(i, 7, QtWidgets.QTableWidgetItem(row['category'] or ''))

                    # Apply background color to all cells in the row
                    if bg_color:
                        for col in range(self.table.columnCount()):
                            self.table.item(i, col).setBackground(bg_color)

                self.table.resizeColumnsToContents()
                self.update_status_bar()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al cargar datos: {e}")
        finally:
            conn.close()

    def update_status_bar(self):
        """Show total items, expiring soon, low stock in status bar."""
        conn = database.get_connection()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM medications")
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM medications WHERE expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'")
                expiring = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM medications WHERE quantity < 5")
                low = cur.fetchone()[0]
                self.status_bar.showMessage(f"📦 Total: {total}   ⏳ Próximos a vencer: {expiring}   ⚠️ Stock bajo: {low}")
        except Exception:
            pass
        finally:
            conn.close()

    def get_selected_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.table.item(row, 0).text())

    def add_medication(self):
        dlg = add_edit_dialog.AddEditDialog(self, None)
        dlg.exec_()
        self.load_data()

    def edit_medication(self):
        med_id = self.get_selected_id()
        if med_id is None:
            QtWidgets.QMessageBox.warning(self, "Seleccionar", "Seleccione un medicamento.")
            return
        conn = database.get_connection()
        if not conn:
            return
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM medications WHERE id = %s", (med_id,))
                med = cur.fetchone()
                if med:
                    dlg = add_edit_dialog.AddEditDialog(self, med)
                    dlg.exec_()
                    self.load_data()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al obtener datos: {e}")
        finally:
            conn.close()

    def delete_medication(self):
        med_id = self.get_selected_id()
        if med_id is None:
            return
        row = self.table.selectedItems()[0].row()
        med_name = self.table.item(row, 1).text()
        reply = QtWidgets.QMessageBox.question(self, "Confirmar", f"¿Eliminar {med_name}?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            conn = database.get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM medications WHERE id = %s", (med_id,))
                        conn.commit()
                    self.load_data()
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Error al eliminar: {e}")
                finally:
                    conn.close()

    def show_alerts(self):
        dlg = alerts_dialog.AlertsDialog(self)
        dlg.exec_()

    def export_csv(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar CSV", "", "CSV files (*.csv)")
        if filename:
            helpers.export_table_to_csv(self.table, filename)
            QtWidgets.QMessageBox.information(self, "Exportar", "Datos exportados correctamente.")

    def check_alerts_and_notify(self):
        """Check for expiring and low stock items and show a notification if any."""
        conn = database.get_connection()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                today = date.today()
                limit = today + timedelta(days=30)
                cur.execute("SELECT COUNT(*) FROM medications WHERE expiration_date BETWEEN %s AND %s", (today, limit))
                expiring = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM medications WHERE quantity < 5")
                low = cur.fetchone()[0]
                if expiring > 0 or low > 0:
                    msg = f"Se encontraron alertas:\n\n"
                    if expiring > 0:
                        msg += f"• {expiring} medicamento(s) próximo(s) a vencer (30 días).\n"
                    if low > 0:
                        msg += f"• {low} medicamento(s) con stock bajo (<5).\n"
                    msg += "\n¿Desea ver las alertas ahora?"
                    reply = QtWidgets.QMessageBox.question(self, "Alertas de Inventario", msg,
                                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if reply == QtWidgets.QMessageBox.Yes:
                        self.show_alerts()
        except Exception as e:
            print(f"Error checking alerts: {e}")
        finally:
            conn.close()