import subprocess
import sys


def install_pyqt5() -> None:
    try:
        import PyQt5
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyQt5'])


def install_owslib() -> None:
    try:
        import owslib
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'owslib'])
