import sys
import pandas as pd
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, \
    QFrame, QGridLayout, QSizePolicy, QTextEdit, QFileDialog
from PySide2.QtGui import QFontMetrics
from PySide2.QtCore import Qt


class VonMisesMaxApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Von Mises Max Calculator")

        # Create main widget and layout
        self.main_widget = QWidget()
        self.layout = QGridLayout(self.main_widget)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)

        # Create labels and text inputs for the fields
        self.labels = [
            "d", "Zx", "Sx", "Ix", "Iy", "Zy", "Sy", "A"
        ]
        self.text_inputs = {}

        for index, label in enumerate(self.labels):
            self.create_label_and_text_input(label, index)

        # Create von Mises Max button
        self.von_mises_button = QPushButton("Calculate von Mises Max")
        self.von_mises_button.clicked.connect(self.calculate_von_mises_max)
        self.layout.addWidget(self.von_mises_button, 0, 0, 1, 2)

        # Create load DataFrame button
        self.load_button = QPushButton("Load DataFrame")
        self.load_button.clicked.connect(self.load_dataframe)
        self.layout.addWidget(self.load_button, 1, 0, 1, 2)

        # Create frame for displaying DataFrame
        self.data_frame_frame = QFrame()
        self.data_frame_frame.setFrameShape(QFrame.StyledPanel)
        self.data_frame_frame.setFrameShadow(QFrame.Raised)
        self.data_frame_layout = QVBoxLayout(self.data_frame_frame)
        self.data_frame_text_edit = QTextEdit()
        self.data_frame_text_edit.setReadOnly(True)
        self.data_frame_layout.addWidget(self.data_frame_text_edit)

        # Add frame to the layout
        self.layout.addWidget(self.data_frame_frame, 2, 0, 1, 2)

        # Set the main widget as the central widget
        self.setCentralWidget(self.main_widget)

    def create_label_and_text_input(self, label_text, row):
        label = QLabel(label_text)
        text_input = QLineEdit()
        text_input.setFixedWidth(150)

        self.layout.addWidget(label, row, 0)
        self.layout.addWidget(text_input, row, 1)

        self.text_inputs[label_text] = text_input

    def calculate_von_mises_max(self):
        # Retrieve values from the text inputs
        d = float(self.text_inputs["d"].text())
        Zx = float(self.text_inputs["Zx"].text())
        Sx = float(self.text_inputs["Sx"].text())
        Ix = float(self.text_inputs["Ix"].text())
        Iy = float(self.text_inputs["Iy"].text())
        Zy = float(self.text_inputs["Zy"].text())
        Sy = float(self.text_inputs["Sy"].text())
        A = float(self.text_inputs["A"].text())

        # Perform the calculation of von Mises Max using the retrieved values
        # Replace the calculation below with your actual von Mises Max calculation
        von_mises_max = (Zx + Sx + Ix + Iy + Zy + Sy + A) / d

        # Display the result
        print("von Mises Max:", von_mises_max)

    def load_dataframe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Text File", "", "Text Files (*.txt)")

        if file_path:
            try:
                dataframe = pd.read_csv(file_path, delimiter='\t')  # Assuming tab-separated values
                self.display_dataframe(dataframe)
            except Exception as e:
                print("Error loading DataFrame:", str(e))

    def display_dataframe(self, dataframe):
        self.data_frame_text_edit.clear()
        self.data_frame_text_edit.setPlainText(dataframe.to_string())

        # Adjust the font size to fit the frame width
        font = self.data_frame_text_edit.font()
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(dataframe.to_string())
        frame_width = self.data_frame_frame.width()
        scale_factor = 0.9

        if text_width > frame_width:
            font.setPointSizeF(font.pointSizeF() * scale_factor)
            self.data_frame_text_edit.setFont(font)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    von_mises_app = VonMisesMaxApp()
    von_mises_app.show()
    sys.exit(app.exec_())