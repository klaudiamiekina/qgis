import os
import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, \
    QFileDialog, QDialog


class ConverterGui(QDialog):
    def __init__(self, parent, qgis_instance_dir):
        super().__init__()
        self.initUI()
        self.parent = parent
        self.qgis_instance_dir = qgis_instance_dir
        self.dialog_values = []

    def initUI(self):
        self.setWindowTitle('Program do konwersji pliku .aprx do pliku .qgs')
        self.setGeometry(100, 100, 500, 200)

        self.file_path = QLineEdit(self)
        self.file_path.setPlaceholderText('Ścieżka do pliku .aprx')
        self.folder_path = QLineEdit(self)
        self.folder_path.setPlaceholderText('Ścieżka do folderu zapisu projektu QGIS')
        self.qgis_file_name = QLineEdit(self)
        self.qgis_file_name.setPlaceholderText('Nazwa projektu QGIS')

        self.browse_file_button = QPushButton('Przeglądaj plik', self)
        self.browse_file_button.clicked.connect(self.browse_file)
        self.browse_folder_button = QPushButton('Przeglądaj folder', self)
        self.browse_folder_button.clicked.connect(self.browse_folder)

        self.validate_button = QPushButton('Uruchom program', self)
        self.validate_button.clicked.connect(self.validate_paths)

        self.result_label = QLabel(self)

        self.v_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()
        h_layout3 = QHBoxLayout()

        h_layout1.addWidget(self.file_path)
        h_layout1.addWidget(self.browse_file_button)
        h_layout2.addWidget(self.folder_path)
        h_layout2.addWidget(self.browse_folder_button)
        h_layout3.addWidget(self.qgis_file_name)

        self.v_layout.addLayout(h_layout1)
        self.v_layout.addLayout(h_layout2)
        self.v_layout.addLayout(h_layout3)
        self.v_layout.addWidget(self.validate_button)
        self.v_layout.addWidget(self.result_label)

        self.setLayout(self.v_layout)

        self.result_label.setText('')

    def browse_file(self):
        file_filter = "aprx(*.aprx)"
        file_path, _ = QFileDialog.getOpenFileName(self, 'Wybierz plik', filter=file_filter)
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
            self.remove_red_frame(self.file_path)
            self.remove_red_frame(self.folder_path)
            self.remove_red_frame(self.qgis_file_name)
            self.result_label.setText('')
            for button in (self.browse_file_button, self.browse_folder_button, self.validate_button):
                button.setEnabled(False)
            self.dump_to_json()
            self.parent.run_converter_qgis()

    def dump_to_json(self):
        aprx_properties = {
            'arcgis_file_path': self.file_path.text(),
            'qgis_folder_path': self.folder_path.text(),
            'qgis_file_name': self.qgis_file_name.text(),
            'qgis_instance_dir': self.qgis_instance_dir
        }
        self.parent.dump_aprx_properties_to_json(f'{self.parent.arcgis_project_dir}\\properties_for_qgis_project.json',
                                                 aprx_properties)

    def add_label_after_conversion(self):
        with open(f'{self.parent.arcgis_project_dir}\\saved_files.txt', 'r') as saved_files:
            created_files = saved_files.readlines()
            created_files = ''.join(created_files)
        self.result_label.setText(f'Operacja wykonana pomyślnie!\n'
                                  f'W wyniku działania programu, w ścieżce {self.folder_path.text()} '
                                  f'zostały utworzone następujące pliki:\n{created_files}')
        os.remove(f'{self.parent.arcgis_project_dir}\\saved_files.txt')


class ExecDialog:
    def __init__(self, parent, qgis_instance_dir):
        self.parent = parent
        self.qgis_instance_dir = qgis_instance_dir

    def exec_dlg(self):
        app = QApplication(sys.argv)
        self.window = ConverterGui(self.parent, self.qgis_instance_dir)
        self.window.show()
        sys.exit(app.exec_())
