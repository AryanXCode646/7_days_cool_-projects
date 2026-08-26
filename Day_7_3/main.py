import sys
import os
import ctypes

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('30days.day73.typinganalyzer.pro')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from ui import TypingApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create distinct app icon for taskbar and titlebar
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#ff6b6b"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 16, 16)
    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Segoe UI Emoji", 26, QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "⌨")
    painter.end()
    
    icon = QIcon(pixmap)
    app.setWindowIcon(icon)
    
    window = TypingApp()
    window.setWindowIcon(icon)
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec_())