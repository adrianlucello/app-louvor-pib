import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from ui.main_window import MainWindow
import qdarkstyle

if __name__ == "__main__":
    # Enable high DPI scaling and high-DPI pixmaps for crisp icons on retina displays
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
