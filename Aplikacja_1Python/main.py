from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QTableWidget, \
    QTableWidgetItem, QInputDialog
import json

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class DataStorage(metaclass=SingletonMeta):
    def __init__(self):
        self.car_model = None
        self.incidents_count = None

    def save_to_file(self):
        data = {
            "car_model": self.car_model,
            "incidents_count": self.incidents_count
        }
        with open("data.json", "w") as file:
            json.dump(data, file)

    def load_from_file(self):
        try:
            with open("data.json", "r") as file:
                data = json.load(file)
                self.car_model = data.get("car_model")
                self.incidents_count = data.get("incidents_count")
        except FileNotFoundError:
            # Handle the case when the file does not exist
            pass

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select a Racing Game")

        layout = QVBoxLayout()

        button_project_cars = QPushButton("Project Cars 2")
        button_project_cars.clicked.connect(lambda: self.show_game_options("Project Cars 2"))
        layout.addWidget(button_project_cars)

        button_iracing = QPushButton("iRacing")
        button_iracing.clicked.connect(lambda: self.show_game_options("iRacing"))
        layout.addWidget(button_iracing)

        self.setLayout(layout)

    def show_game_options(self, game_name):
        if game_name == "Project Cars 2":
            project_cars_options_window = ProjectCarsOptionsWindow(self)
            project_cars_options_window.exec()
        elif game_name == "iRacing":
            iracing_options_window = IRacingOptionsWindow(self)
            iracing_options_window.exec()

class ProjectCarsOptionsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Project Cars 2 Options")

        layout = QVBoxLayout()

        button_stats = QPushButton("Twoje statystyki")
        button_stats.clicked.connect(self.show_stats)
        layout.addWidget(button_stats)

        button_add_results = QPushButton("Dodaj wyniki")
        button_add_results.clicked.connect(self.show_add_results_options)
        layout.addWidget(button_add_results)

        button_leaderboard = QPushButton("Ranking światowy")
        layout.addWidget(button_leaderboard)

        button_back = QPushButton("Powrót do wyboru gry")
        button_back.clicked.connect(self.accept)
        layout.addWidget(button_back)

        # Initialize the QTableWidget here, but don't show it initially
        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Model auta", "Pozycja w wyścigu", "Ilość incydentów"])

        # Add the results_table to the layout
        layout.addWidget(self.results_table)

        self.setLayout(layout)

        # Load data from file on initialization
        data_storage = DataStorage()
        data_storage.load_from_file()

    def show_stats(self):
        data_storage = DataStorage()
        if data_storage.car_model:
            self.populate_results_table()
            # Show the table only when stats are available
            self.results_table.show()

    def show_add_results_options(self):
        add_results_options_window = AddResultsOptionsWindow(self)
        add_results_options_window.exec()

    def populate_results_table(self):
        data_storage = DataStorage()
        # Assuming you have a data structure to store the latest results
        latest_results = [(data_storage.car_model, "1st",
                            str(data_storage.incidents_count) if data_storage.incidents_count is not None else "")]

        # Clear the existing content
        self.results_table.setRowCount(0)

        # Populate the table with the latest results
        for row, (car_model, position, incidents_count) in enumerate(latest_results):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(car_model))
            self.results_table.setItem(row, 1, QTableWidgetItem(position))
            self.results_table.setItem(row, 2, QTableWidgetItem(incidents_count))

class AddResultsOptionsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opcje Dodaj wyniki")

        layout = QVBoxLayout()

        button_position = QPushButton("Pozycja w wyścigu")
        layout.addWidget(button_position)
        button_position.clicked.connect(lambda: self.handle_option("Pozycja w wyścigu"))

        button_car_model = QPushButton("Model auta")
        button_car_model.clicked.connect(self.get_car_model)
        layout.addWidget(button_car_model)

        button_incidents = QPushButton("Ilość incydentów")
        button_incidents.clicked.connect(self.get_incidents_count)
        layout.addWidget(button_incidents)

        back_button = QPushButton("Powrót do opcji Project Cars 2")
        back_button.clicked.connect(self.accept)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def handle_option(self, option):
        print(f"Wybrana opcja: {option}")

    def get_car_model(self):
        car_model, ok_pressed = QInputDialog.getText(self, "Model auta", "Wprowadź model auta:")
        if ok_pressed and car_model:
            data_storage = DataStorage()
            data_storage.car_model = car_model

    def get_incidents_count(self):
        incidents_count, ok_pressed = QInputDialog.getInt(self, "Ilość incydentów", "Wprowadź ilość incydentów:", 0, 0, 100)
        if ok_pressed:
            data_storage = DataStorage()
            data_storage.incidents_count = incidents_count

class IRacingOptionsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("iRacing Options")

        layout = QVBoxLayout()

        button_stats = QPushButton("Twoje statystyki")
        layout.addWidget(button_stats)

        button_add_results = QPushButton("Dodaj wyniki")
        button_add_results.clicked.connect(self.show_add_results_options)
        layout.addWidget(button_add_results)

        layout.addWidget(QPushButton("Ranking światowy"))

        button_back = QPushButton("Powrót do wyboru gry")
        button_back.clicked.connect(self.accept)
        layout.addWidget(button_back)

        self.setLayout(layout)

    def show_add_results_options(self):
        add_results_options_window = AddResultsOptionsWindow(self)
        add_results_options_window.exec()

if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
