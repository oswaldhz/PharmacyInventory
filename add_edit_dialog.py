from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
import database
from datetime import datetime, date

class TitleBar(QtWidgets.QWidget):
    """Custom title bar with gradient and animated buttons."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2b2b2b, stop:1 #3c3c3c);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)

        # Icon
        icon_label = QtWidgets.QLabel("💊")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Minimize button
        self.min_btn = self.create_title_button("–", "#3c3c3c", "#5a5a5a")
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

        # Maximize/Restore button
        self.max_btn = self.create_title_button("□", "#3c3c3c", "#5a5a5a")
        self.max_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.max_btn)

        # Close button
        self.close_btn = self.create_title_button("×", "#c42b2b", "#e04343")
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.close_btn)

        self.drag_pos = None

    def create_title_button(self, text, normal_color, hover_color):
        btn = QtWidgets.QPushButton(text)
        btn.setFixedSize(30, 30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {normal_color};
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        return btn

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            delta = event.globalPos() - self.drag_pos
            self.parent.move(self.parent.pos() + delta)
            self.drag_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.max_btn.setText("□")
        else:
            self.parent.showMaximized()
            self.max_btn.setText("❐")

class AnimatedLineEdit(QtWidgets.QLineEdit):
    """Line edit with focus glow animation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #4a6b8a;
            }
        """)

class AddEditDialog(QtWidgets.QDialog):
    def __init__(self, main_window, medication=None):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Window)  # No parent for independent window
        self.main_window = main_window
        self.medication = medication
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(550, 500)
        self.setMaximumSize(800, 600)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        title = "Agregar Medicamento" if medication is None else "Editar Medicamento"
        self.title_bar = TitleBar(self, title)
        main_layout.addWidget(self.title_bar)

        # Content widget with gradient background
        content = QtWidgets.QWidget()
        content.setObjectName("DialogContent")
        content.setStyleSheet("""
            QWidget#DialogContent {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2b2b2b, stop:1 #3c3c3c);
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        main_layout.addWidget(content)

        # Form layout
        form_layout = QtWidgets.QFormLayout(content)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(30, 30, 30, 30)

        self.categories = []
        self.load_categories()

        # Name
        self.name_edit = AnimatedLineEdit()
        self.name_edit.setFixedHeight(35)
        if medication:
            self.name_edit.setText(medication['name'])
        form_layout.addRow("Nombre *:", self.name_edit)

        # Code
        self.code_edit = AnimatedLineEdit()
        self.code_edit.setFixedHeight(35)
        if medication:
            self.code_edit.setText(medication['code'])
        form_layout.addRow("Código *:", self.code_edit)

        # Lot
        self.lot_edit = AnimatedLineEdit()
        self.lot_edit.setFixedHeight(35)
        if medication and medication['lot']:
            self.lot_edit.setText(medication['lot'])
        form_layout.addRow("Lote:", self.lot_edit)

        # Expiration date
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setFixedHeight(35)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QtCore.QDate.currentDate())
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
        """)
        if medication and medication['expiration_date']:
            qdate = QtCore.QDate(medication['expiration_date'].year,
                                 medication['expiration_date'].month,
                                 medication['expiration_date'].day)
            self.date_edit.setDate(qdate)
        form_layout.addRow("Vencimiento *:", self.date_edit)

        # Price
        self.price_edit = AnimatedLineEdit()
        self.price_edit.setFixedHeight(35)
        if medication:
            self.price_edit.setText(f"{medication['price']:.2f}")
        form_layout.addRow("Precio:", self.price_edit)

        # Quantity
        self.qty_edit = AnimatedLineEdit()
        self.qty_edit.setFixedHeight(35)
        if medication:
            self.qty_edit.setText(str(medication['quantity']))
        form_layout.addRow("Cantidad *:", self.qty_edit)

        # Category
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.setFixedHeight(35)
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.category_combo.addItem("")
        for cid, name in self.categories:
            self.category_combo.addItem(name, cid)
        if medication and medication['category_id']:
            index = self.category_combo.findData(medication['category_id'])
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        form_layout.addRow("Categoría:", self.category_combo)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.save_btn = QtWidgets.QPushButton("Guardar")
        self.save_btn.setFixedSize(120, 40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6b8a;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a7b9a;
            }
            QPushButton:pressed {
                background-color: #3a5b7a;
            }
        """)
        self.save_btn.clicked.connect(self.validate_and_accept)

        self.cancel_btn = QtWidgets.QPushButton("Cancelar")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        form_layout.addRow(button_layout)

        # Shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        # Center on main window
        self.adjustSize()
        if main_window:
            self.move(main_window.geometry().center() - self.rect().center())

    def load_categories(self):
        conn = database.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, name FROM categories ORDER BY name")
                    self.categories = cur.fetchall()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Error al cargar categorías: {e}")
            finally:
                conn.close()

    def validate_and_accept(self):
        name = self.name_edit.text().strip()
        code = self.code_edit.text().strip()
        qty_str = self.qty_edit.text().strip()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        price_str = self.price_edit.text().strip()

        if not name or not code or not qty_str:
            QtWidgets.QMessageBox.warning(self, "Validación", "Nombre, Código y Cantidad son obligatorios.")
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Validación", "Cantidad debe ser un número entero mayor que cero.")
            return

        try:
            exp_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if exp_date <= date.today():
                QtWidgets.QMessageBox.warning(self, "Validación", "Fecha de vencimiento debe ser posterior a hoy.")
                return
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Validación", "Fecha inválida.")
            return

        try:
            price = float(price_str) if price_str else 0.0
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Validación", "Precio debe ser un número válido.")
            return

        conn = database.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if self.medication:
                        cur.execute("SELECT id FROM medications WHERE code = %s AND id != %s", (code, self.medication['id']))
                    else:
                        cur.execute("SELECT id FROM medications WHERE code = %s", (code,))
                    if cur.fetchone():
                        QtWidgets.QMessageBox.warning(self, "Validación", "Ya existe un medicamento con ese código.")
                        return
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Error de base de datos: {e}")
                return
            finally:
                conn.close()

        self.accept()
        self.save_medication(name, code, self.lot_edit.text().strip() or None,
                             exp_date, price, qty, self.category_combo.currentData())

    def save_medication(self, name, code, lot, exp_date, price, quantity, category_id):
        conn = database.get_connection()
        if not conn:
            QtWidgets.QMessageBox.critical(self, "Error", "No se pudo conectar a la base de datos.")
            return
        try:
            with conn.cursor() as cur:
                if self.medication:
                    cur.execute("""
                        UPDATE medications
                        SET name=%s, code=%s, lot=%s, expiration_date=%s,
                            price=%s, quantity=%s, category_id=%s
                        WHERE id=%s
                    """, (name, code, lot, exp_date, price, quantity, category_id, self.medication['id']))
                else:
                    cur.execute("""
                        INSERT INTO medications (name, code, lot, expiration_date, price, quantity, category_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (name, code, lot, exp_date, price, quantity, category_id))
                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            conn.close()