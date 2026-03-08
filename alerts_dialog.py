from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import database
from datetime import date, timedelta
from psycopg2 import extras

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

        icon_label = QtWidgets.QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.min_btn = self.create_title_button("–", "#3c3c3c", "#5a5a5a")
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

        self.max_btn = self.create_title_button("□", "#3c3c3c", "#5a5a5a")
        self.max_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.max_btn)

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

class AlertsDialog(QtWidgets.QDialog):
    def __init__(self, main_window):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Window)
        self.main_window = main_window
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(900, 600)
        self.setMaximumSize(1200, 800)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self, "Alertas de Inventario")
        main_layout.addWidget(self.title_bar)

        # Content widget with gradient
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

        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3c3c3c, stop:1 #2b2b2b);
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 8px 15px;
                margin-right: 2px;
                color: #e0e0e0;
            }
            QTabBar::tab:selected {
                background: #4a6b8a;
            }
            QTabBar::tab:hover {
                background: #4a4a4a;
            }
        """)
        layout.addWidget(self.tabs)

        # Tab 1: Near expiry
        self.expiry_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.expiry_tab, "Próximos a vencer (30 días)")
        self.create_table(self.expiry_tab, ['Nombre', 'Código', 'Vence'])

        # Tab 2: Low stock
        self.low_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.low_tab, "Stock bajo (<5)")
        self.create_table(self.low_tab, ['Nombre', 'Código', 'Stock'])

        # Refresh button
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        self.refresh_btn = QtWidgets.QPushButton("Actualizar")
        self.refresh_btn.setFixedSize(140, 40)
        self.refresh_btn.setStyleSheet("""
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
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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

        self.load_data()

    def create_table(self, tab, headers):
        layout = QtWidgets.QVBoxLayout(tab)
        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)

        # Enhanced stylesheet to ensure full dark background
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #3c3c3c;
                gridline-color: transparent;
                selection-background-color: #4a6b8a;
                color: #e0e0e0;
            }
            QTableWidget::item {
                background-color: #2b2b2b;
            }
            QTableWidget::item:alternate {
                background-color: #3c3c3c;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #e0e0e0;
            }
            QTableCornerButton::section {
                background-color: #1e1e1e;
                border: none;
            }
            QTableWidget::viewport {
                background-color: #2b2b2b;
            }
        """)
        layout.addWidget(table)
        setattr(self, f"table_{tab.objectName() if tab.objectName() else 'expiry' if tab==self.expiry_tab else 'low'}", table)

    def load_data(self):
        for table in [self.table_expiry, self.table_low]:
            table.setRowCount(0)

        conn = database.get_connection()
        if not conn:
            QtWidgets.QMessageBox.critical(self, "Error", "No se pudo conectar a la base de datos.")
            return
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                today = date.today()
                limit = today + timedelta(days=30)
                cur.execute("""
                    SELECT name, code, expiration_date
                    FROM medications
                    WHERE expiration_date BETWEEN %s AND %s
                    ORDER BY expiration_date
                """, (today, limit))
                rows = cur.fetchall()
                self.table_expiry.setRowCount(len(rows) if rows else 1)
                if not rows:
                    item = QtWidgets.QTableWidgetItem("No hay medicamentos próximos a vencer.")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_expiry.setItem(0, 0, item)
                else:
                    for i, row in enumerate(rows):
                        self.table_expiry.setItem(i, 0, QtWidgets.QTableWidgetItem(row['name']))
                        self.table_expiry.setItem(i, 1, QtWidgets.QTableWidgetItem(row['code']))
                        self.table_expiry.setItem(i, 2, QtWidgets.QTableWidgetItem(row['expiration_date'].strftime('%Y-%m-%d')))
                        # Color the row orange
                        for col in range(3):
                            self.table_expiry.item(i, col).setBackground(QtGui.QColor(200, 130, 50))

                cur.execute("""
                    SELECT name, code, quantity
                    FROM medications
                    WHERE quantity < 5
                    ORDER BY quantity
                """)
                rows = cur.fetchall()
                self.table_low.setRowCount(len(rows) if rows else 1)
                if not rows:
                    item = QtWidgets.QTableWidgetItem("No hay medicamentos con stock bajo.")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_low.setItem(0, 0, item)
                else:
                    for i, row in enumerate(rows):
                        self.table_low.setItem(i, 0, QtWidgets.QTableWidgetItem(row['name']))
                        self.table_low.setItem(i, 1, QtWidgets.QTableWidgetItem(row['code']))
                        self.table_low.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row['quantity'])))
                        # Color the row red
                        for col in range(3):
                            self.table_low.item(i, col).setBackground(QtGui.QColor(200, 70, 70))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al cargar alertas: {e}")
        finally:
            conn.close()