import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, \
    QFileDialog, QDialog


# from main import run_qgs_converter


class MyQtGUI(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self._dialog_values = []

    def initUI(self):
        self.setWindowTitle('Program do konwersji pliku .aprx do pliku .qgs')
        self.setGeometry(100, 100, 400, 200)

        self.file_path = QLineEdit(self)
        self.file_path.setPlaceholderText('Ścieżka do pliku')
        self.folder_path = QLineEdit(self)
        self.folder_path.setPlaceholderText('Ścieżka do folderu')
        self.qgis_file_name = QLineEdit(self)
        self.qgis_file_name.setPlaceholderText('Nazwa projektu QGIS')

        self.browse_file_button = QPushButton('Przeglądaj plik', self)
        self.browse_file_button.clicked.connect(self.browse_file)
        self.browse_folder_button = QPushButton('Przeglądaj folder', self)
        self.browse_folder_button.clicked.connect(self.browse_folder)

        self.validate_button = QPushButton('Zatwierdź', self)
        self.validate_button.clicked.connect(self.validate_paths)

        self.result_label = QLabel(self)

        v_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()
        h_layout3 = QHBoxLayout()

        h_layout1.addWidget(self.file_path)
        h_layout1.addWidget(self.browse_file_button)
        h_layout2.addWidget(self.folder_path)
        h_layout2.addWidget(self.browse_folder_button)
        h_layout3.addWidget(self.qgis_file_name)

        v_layout.addLayout(h_layout1)
        v_layout.addLayout(h_layout2)
        v_layout.addLayout(h_layout3)
        v_layout.addWidget(self.validate_button)
        v_layout.addWidget(self.result_label)

        self.setLayout(v_layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Wybierz plik')
        if file_path:
            self.file_path.setText(file_path)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Wybierz folder')
        if folder_path:
            self.folder_path.setText(folder_path)

    def apply_red_frame(self, line_edit):
        line_edit.setStyleSheet('border: 1px solid red;')

    def remove_red_frame(self, line_edit):
        line_edit.setStyleSheet('')

    def validate_paths(self):
        file_path = self.file_path.text()
        folder_path = self.folder_path.text()
        self.result_label.setText('')
        self.remove_red_frame(self.file_path)
        self.remove_red_frame(self.folder_path)
        self.remove_red_frame(self.qgis_file_name)

        if not os.path.isfile(file_path):
            self.apply_red_frame(self.file_path)
            self.result_label.setText('Uwaga! W systemie nie odnaleziono pliku o podanej ścieżce!')
        if not os.path.isdir(folder_path):
            self.apply_red_frame(self.folder_path)
            self.result_label.setText('Uwaga! W systemie nie odnaleziono folderu o podanej ścieżce!')

        if all((not os.path.isfile(file_path), not os.path.isdir(folder_path))):
            self.result_label.setText('Uwaga! Przed zatwierdzeniem zmian proszę '
                                      'poprawnie uzupełnić podświetlone elementy!')

        for line_edit in (self.file_path, self.folder_path, self.qgis_file_name):
            if not bool(line_edit.text()):
                self.apply_red_frame(line_edit)
                self.result_label.setText('Uwaga! Przed zatwierdzeniem zmian proszę '
                                          'poprawnie uzupełnić podświetlone elementy!')

        if all((os.path.isfile(file_path), os.path.isdir(folder_path), self.qgis_file_name.text())):
            self.accept()

    def accept(self):
        self._dialog_values = self.file_path.text(), self.folder_path.text(), self.qgis_file_name.text()
        super(MyQtGUI, self).accept()


def exec_dialog():
    app = QApplication(sys.argv)
    window = MyQtGUI()
    window.show()
    if window.exec_():
        return window._dialog_values
    sys.exit(app.exec_())


vals = exec_dialog()

