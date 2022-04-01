import sys

from gui import *

if __name__ == "__main__":
    thisApp = QApplication(sys.argv)
    window = ProgressWindow()
    window.show()
    try:
        sys.exit(thisApp.exec())
    except KeyboardInterrupt:
        sys.exit()