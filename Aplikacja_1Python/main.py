from PySide6.QtCore import Signal, QTimer, QObject
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QTableWidget, \
    QTableWidgetItem, QInputDialog
import json

class SignalHandler(QObject):
    showStatsSignal = Signal()

class RaceResult:
    def __init__(self, *args):
        self.car_model, self.incidents_count, self.position_in_race, self.track_name = args

class DataStorage:
    def __init__(self):
        self.car_model = None
        self.incidents_count = None
        self.position_in_race = None
        self.track_name = None
        self.results_history = []  # Now storing results history as RaceResult objects
        self.max_results_history = 15

    def save_to_file(self):
        data = {
            "car_model": self.car_model,
            "incidents_count": self.incidents_count,
            "position_in_race": self.position_in_race,
            "track_name": self.track_name,
            "results_history": [(result.car_model, result.incidents_count, result.position_in_race, result.track_name) for result in self.results_history]
        }
        with open("data.json", "w") as file:
            json.dump(data, file)

    def load_from_file(self):
        try:
            with open("data.json", "r") as file:
                data = json.load(file)
                self.car_model = data.get("car_model")
                self.incidents_count = data.get("incidents_count")
                self.position_in_race = data.get("position_in_race")
                self.track_name = data.get("track_name")
                self.results_history = [RaceResult(*result) for result in data.get("results_history", [])]
        except FileNotFoundError:
            # Handle the case when the file does not exist
            pass

    def add_result_to_history(self, result):
        self.results_history.insert(0, result)
        self.results_history = self.results_history[:self.max_results_history]
        self.save_to_file()

class MainWindow(QWidget):
    showStatsSignal = Signal()

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
            project_cars_options_window.showStatsSignal.connect(self.delayed_show_stats)
            project_cars_options_window.exec()
        elif game_name == "iRacing":
            iracing_options_window = IRacingOptionsWindow(self)
            iracing_options_window.showStatsSignal.connect(self.delayed_show_stats)
            iracing_options_window.exec()

    def delayed_show_stats(self):
        QTimer.singleShot(0, self.show_stats)

    def show_stats(self):
        self.showStatsSignal.emit()

class ProjectCarsOptionsWindow(QDialog):
    showStatsSignal = Signal()

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

        self.results_table = None  # Do not initialize the table here

        self.setLayout(layout)

    def show_stats(self):
        self.showStatsSignal.emit()

    def show_add_results_options(self):
        add_results_options_window = AddResultsOptionsWindow(self)
        add_results_options_window.showStatsSignal.connect(self.show_stats)
        add_results_options_window.exec()

    def initialize_results_table(self):
        # Initialize the QTableWidget here
        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(4)  # Added a column for the track_name
        self.results_table.setHorizontalHeaderLabels(["Model auta", "Ilość incydentów", "Pozycja w wyniku", "Tor"])

        # Add the results_table to the layout
        layout = self.layout()
        layout.addWidget(self.results_table)

    def populate_results_table(self):
        data_storage = DataStorage()
        # Assuming you have a data structure to store the latest results
        latest_results = [(data_storage.car_model, str(data_storage.incidents_count),
                            str(data_storage.position_in_race) if data_storage.position_in_race is not None else "",
                            data_storage.track_name if data_storage.track_name is not None else "")]

        # Populate the table with the latest results
        for row, (car_model, incidents_count, position_in_race, track_name) in enumerate(latest_results):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(car_model))
            self.results_table.setItem(row, 1, QTableWidgetItem(incidents_count))
            self.results_table.setItem(row, 2, QTableWidgetItem(position_in_race))
            self.results_table.setItem(row, 3, QTableWidgetItem(track_name))

class AddResultsOptionsWindow(QDialog):
    showStatsSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opcje Dodaj wyniki")

        layout = QVBoxLayout()

        button_car_model = QPushButton("Model auta")
        button_car_model.clicked.connect(self.get_car_model)
        layout.addWidget(button_car_model)

        button_incidents = QPushButton("Ilość incydentów")
        button_incidents.clicked.connect(self.get_incidents_count)
        layout.addWidget(button_incidents)

        button_position = QPushButton("Pozycja w wyniku")
        button_position.clicked.connect(self.get_position_in_race)
        layout.addWidget(button_position)

        button_track_name = QPushButton("Tor")
        button_track_name.clicked.connect(self.get_track_name)
        layout.addWidget(button_track_name)

        back_button = QPushButton("Powrót do opcji Project Cars 2")
        back_button.clicked.connect(self.accept)
        layout.addWidget(back_button)

        self.setLayout(layout)

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

    def get_position_in_race(self):
        position_in_race, ok_pressed = QInputDialog.getInt(self, "Pozycja w wyniku", "Wprowadź pozycję w wyniku:", 1, 1, 100)
        if ok_pressed:
            data_storage = DataStorage()
            data_storage.position_in_race = position_in_race

    def get_track_name(self):
        track_name, ok_pressed = QInputDialog.getText(self, "Tor", "Wprowadź nazwę toru:")
        if ok_pressed and track_name:
            data_storage = DataStorage()
            data_storage.track_name = track_name

        self.showStatsSignal.emit()  # Emit signal after getting all data

class IRacingOptionsWindow(QDialog):
    showStatsSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("iRacing Options")

        layout = QVBoxLayout()

        button_stats = QPushButton("Twoje statystyki")
        button_stats.clicked.connect(self.show_stats)
        layout.addWidget(button_stats)

        button_add_results = QPushButton("Dodaj wyniki")
        button_add_results.clicked.connect(self.show_add_results_options)
        layout.addWidget(button_add_results)

        layout.addWidget(QPushButton("Ranking światowy"))

        button_back = QPushButton("Powrót do wyboru gry")
        button_back.clicked.connect(self.accept)
        layout.addWidget(button_back)

        self.setLayout(layout)

    def show_stats(self):
        self.showStatsSignal.emit()

    def show_add_results_options(self):
        add_results_options_window = AddResultsOptionsWindow(self)
        add_results_options_window.showStatsSignal.connect(self.show_stats)
        add_results_options_window.exec()

if __name__ == "__main__":
    app = QApplication([])

    main_window = MainWindow()
    main_window.showStatsSignal.connect(main_window.delayed_show_stats)  # Połączenie sygnału z metodą delayed_show_stats
    main_window.show()

    app.exec()
