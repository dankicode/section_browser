import sys
import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog
from PySide6.QtCore import Qt
from section_browser import w_sections as wsec

def launch_gui_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SectionBrowser - AISC W-sections")
        self.setGeometry(100, 100, 800, 600)

        # Create the main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Create the top widget and layout
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Create the first input section
        input1_widget = QWidget()
        input1_layout = QHBoxLayout(input1_widget)
        self.input1_fields = self.create_input_fields(input1_layout, "Input 1")

        # Create the second input section
        input2_widget = QWidget()
        input2_layout = QHBoxLayout(input2_widget)
        self.input2_fields = self.create_input_fields(input2_layout, "Input 2")

        # Add the input sections to the top layout
        top_layout.addWidget(input1_widget)
        top_layout.addWidget(input2_widget)

        # Add the top layout to the main layout
        main_layout.addWidget(top_widget)

        # Create the output section (datatable)
        self.table = QTableWidget(20, 15)
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3", "Column 4", "Column 5",
                                              "Column 6", "Column 7", "Column 8", "Column 9", "Column 10",
                                              "Column 11", "Column 12", "Column 13", "Column 14", "Column 15"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        # Create the bottom buttons
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        self.create_buttons(button_layout)

        # Add the buttons to the main layout
        main_layout.addWidget(button_widget)

    def create_input_fields(self, layout, title):
        fields = []
        if title == "Input 1":
            fields = ["d", "Zx", "Sx", "Ix", "Iy", "Zy", "Sy", "A", "J"]
        elif title == "Input 2":
            fields = ["N", "Mx", "My", "Vx", "Vy", "T"]
        input_fields = []
        for field in fields:
            label = QLabel(field)
            line_edit = QLineEdit()
            layout.addWidget(label)
            layout.addWidget(line_edit)
            input_fields.append(line_edit)
        return input_fields

    def create_buttons(self, layout):
        layout.addStretch()
        load_data_button = QPushButton("Load Data")
        calculate_button = QPushButton("Calculate Max von Mises")
        export_button = QPushButton("Export to Excel")
        layout.addWidget(load_data_button)
        layout.addWidget(calculate_button)
        layout.addWidget(export_button)

        load_data_button.clicked.connect(self.load_data)
        calculate_button.clicked.connect(self.calculate_von_mises)
        export_button.clicked.connect(self.export_to_excel)

    def load_data(self):
        # filename, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "CSV Files (*.csv)")
        # if filename:
            df = wsec.load_aisc_w_sections()
            fields = ["d", "Zx", "Sx", "Ix", "Iy", "Zy", "Sy", "A", "J"]
            filters = {}
            for idx, input_field in enumerate(self.input1_fields):
                field_name = fields[idx]
                try:
                    input_value = float(input_field.text())
                    filters.update({field_name: input_value})
                except ValueError:
                    pass
            filtered_df = wsec.sections_approx_equal(df, "@", **filters)
            # filters = [float(input_field.text()) if input_field.text().replace(".", "").isnumeric() for input_field in self.input1_fields ]
            # filtered_data = data[data[self.input1_fields[0].text()].isin(filters)]
            self.display_data(filtered_df)

    def calculate_von_mises(self):
        fields = ["N", "Mx", "My", "Vx", "Vy", "T"]
        loads = {}
        for idx, input_field in enumerate(self.input2_fields):
            field_name = fields[idx]
            try:
                input_value = float(input_field.text())
                loads.update({field_name: input_value})
            except ValueError:
                pass

        sections_df = self.get_data_from_table()
        acc = []
        for df_idx, row in sections_df.iterrows():
            section = wsec.create_section(row, mesh_size=100)
            max_vm_stress = wsec.max_vonmises_stress(section, **loads)
            row['Max VM'] = max_vm_stress
            acc.append(row)
        self.display_data(pd.DataFrame(acc))

    def export_to_excel(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Excel", "", "Excel Files (*.xlsx)")
        if filename:
            data = self.get_data_from_table()
            data.to_excel(filename, index=False)

    def display_data(self, data):
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(data.columns))
        # Set the column labels
        self.table.setHorizontalHeaderLabels(data.columns.tolist())
        for i, row in enumerate(data.values):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)

    def get_data_from_table(self):
        columns=self.get_table_header()
        data = []
        for i in range(self.table.rowCount()):
            row = [self.convert_to_float(self.table.item(i, j).text()) for j in range(self.table.columnCount())]
            data.append(row)
        df = pd.DataFrame.from_records(data, columns=columns, coerce_float=True)
        return df
    
    def convert_to_float(self, x):
        try:
            y = float(x)
            return y
        except ValueError:
            return x

    def get_table_header(self):
        return [self.table.horizontalHeaderItem(j).text() for j in range(self.table.columnCount())]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())