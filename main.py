import sys
from PyQt5 import QtWidgets
import database
from main_window import MainWindow

def main():
    database.create_database_if_not_exists()
    database.create_tables()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()