from PySide6.QtCore import Signal, QTimer, QObject
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QTableWidget, \
    QTableWidgetItem, QInputDialog, QLabel, QTextEdit, QSizePolicy

import json
from iracingdataapi.client import irDataClient

class SignalHandler(QObject):
    showStatsSignal = Signal()

class RaceResult:
    def __init__(self, *args, **kwargs):
        self.car_model = kwargs.get("car_model", "")
        self.incidents_count = kwargs.get("incidents_count", "")
        self.position_in_race = kwargs.get("position_in_race", "")
        self.track_name = kwargs.get("track_name", "")
        self.irating = kwargs.get("irating", "")

class DataStorage:
    def __init__(self):
        self.car_model = None
        self.incidents_count = None
        self.position_in_race = None
        self.track_name = None
        self.results_history = []  
        self.max_results_history = 15

    def save_to_file(self):
        data = {
            "car_model": self.car_model,
            "incidents_count": self.incidents_count,
            "position_in_race": self.position_in_race,
            "track_name": self.track_name,
            "results_history": [
                {"car_model": result.car_model,
                 "incidents_count": result.incidents_count,
                 "position_in_race": result.position_in_race,
                 "track_name": result.track_name,
                 "irating": result.irating
                 } for result in self.results_history
            ]
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
                self.results_history = [RaceResult(**result) for result in data.get("results_history", [])]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Błąd podczas wczytywania danych z pliku: {e}")

    def add_result_to_history(self, result):
        self.results_history.insert(0, result)
        self.results_history = self.results_history[:self.max_results_history]
        self.save_to_file()


class MainWindow(QWidget):
    showStatsSignal = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Wybierz grę wyścigową")

        layout = QVBoxLayout()

        button_project_cars = QPushButton("Project Cars 2")
        button_project_cars.clicked.connect(lambda: self.show_game_options("Project Cars 2"))
        layout.addWidget(button_project_cars)

        button_iracing = QPushButton("iRacing")
        button_iracing.clicked.connect(lambda: self.show_game_options("iRacing"))
        layout.addWidget(button_iracing)

        self.data_storage = DataStorage()  

        self.setLayout(layout)

    def show_game_options(self, game_name):
        if game_name == "Project Cars 2":
            project_cars_options_window = ProjectCarsOptionsWindow(self.data_storage, self)
            project_cars_options_window.showStatsSignal.connect(project_cars_options_window.populate_results_table)
            project_cars_options_window.showStatsSignal.connect(project_cars_options_window.show_stats)
            project_cars_options_window.exec()
        elif game_name == "iRacing":
            iracing_options_window = IRacingOptionsWindow(self.data_storage, self)
            iracing_options_window.showStatsSignal.connect(iracing_options_window.populate_results_table)
            iracing_options_window.showStatsSignal.connect(iracing_options_window.show_stats)
            iracing_options_window.exec()

    def delayed_show_stats(self):
        QTimer.singleShot(0, self.show_stats)

    def show_stats(self):
        self.showStatsSignal.emit()
class StatsWindow(QDialog):
    def __init__(self, results_history, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Twoje statystyki")

        layout = QVBoxLayout()

        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Model auta", "Ilość incydentów", "Pozycja w wyścigu", "Tor"])

        layout.addWidget(self.results_table)
        self.data_storage = DataStorage()
        self.data_storage.load_from_file()
        self.populate_results_table(results_history)

        self.setLayout(layout)

    def populate_results_table(self, results_history):
        for row, result in enumerate(results_history):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(result.car_model))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(result.incidents_count)))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(result.position_in_race) if result.position_in_race is not None else ""))
            self.results_table.setItem(row, 3, QTableWidgetItem(result.track_name if result.track_name is not None else ""))

class IRacingStatsWindow(StatsWindow):
    def __init__(self, results_history, parent=None):
        super().__init__(results_history, parent)

    # Modyfikacja: Dostosuj funkcję do wyświetlania statystyk iRacing
    def populate_results_table(self, results_history):
        for row, result in enumerate(results_history):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(result.car_model))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(result.incidents_count)))
            
            # Aktualizacja: Sprawdź, czy atrybut 'start_position' istnieje
            start_position = getattr(result, 'start_position', None)
            self.results_table.setItem(row, 2, QTableWidgetItem(str(start_position) if start_position is not None else ""))
            
            # Aktualizacja: Sprawdź, czy atrybut 'end_position' istnieje
            end_position = getattr(result, 'end_position', None)
            self.results_table.setItem(row, 3, QTableWidgetItem(result.track_name if result.track_name is not None else ""))
class ProjectCarsOptionsWindow(QDialog):
    showStatsSignal = Signal()

    def __init__(self, data_storage, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opcje Project Cars 2")

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

        self.results_table = None
        self.data_storage = data_storage  

        self.setLayout(layout)

    def show_stats(self):
        if isinstance(self, IRacingOptionsWindow):
            # Modyfikacja: Wywołaj funkcję związana z opcją "iRacing"
            self.show_iracing_stats()
        else:
            stats_window = StatsWindow(self.data_storage.results_history, self)
            stats_window.exec()

    # Modyfikacja: Dodaj nową funkcję do obsługi statystyk dla iRacing
    def show_iracing_stats(self):
        iracing_stats_window = IRacingStatsWindow(self.data_storage.results_history, self)
        iracing_stats_window.exec()

    def show_add_results_options(self):
        add_results_options_window = AddResultsOptionsWindow(self.data_storage, self)
        add_results_options_window.showStatsSignal.connect(self.show_stats)
        add_results_options_window.exec()

    def initialize_results_table(self):
        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Model auta", "Ilość incydentów", "Pozycja w wyścigu", "Tor"])

    def populate_results_table(self):
        latest_results = self.data_storage.results_history
        self.initialize_results_table()

        for row, result in enumerate(latest_results):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(result.car_model))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(result.incidents_count)))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(result.position_in_race) if result.position_in_race is not None else ""))
            self.results_table.setItem(row, 3, QTableWidgetItem(result.track_name if result.track_name is not None else ""))

        layout = self.layout()
        layout.addWidget(self.results_table)

class AddResultsOptionsWindow(QDialog):
    showStatsSignal = Signal()

    def __init__(self, data_storage, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opcje Dodaj wyniki")

        layout = QVBoxLayout()

        button_car_model = QPushButton("Model auta")
        button_car_model.clicked.connect(self.get_car_model)
        layout.addWidget(button_car_model)

        button_incidents = QPushButton("Ilość incydentów")
        button_incidents.clicked.connect(self.get_incidents_count)
        layout.addWidget(button_incidents)

        button_position = QPushButton("Pozycja w wyścigu")
        button_position.clicked.connect(self.get_position_in_race)
        layout.addWidget(button_position)

        button_track_name = QPushButton("Tor")
        button_track_name.clicked.connect(self.get_track_name)
        layout.addWidget(button_track_name)

        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

        back_button = QPushButton("Powrót do opcji Project Cars 2")
        back_button.clicked.connect(self.accept)
        layout.addWidget(back_button)

        self.data_storage = data_storage
        self.data_storage.load_from_file()
        self.setLayout(layout)

    def get_car_model(self):
        car_model, ok_pressed = QInputDialog.getText(self, "Model auta", "Wprowadź model auta:")
        if ok_pressed and car_model:
            self.data_storage.car_model = car_model

    def get_incidents_count(self):
        incidents_count, ok_pressed = QInputDialog.getInt(self, "Ilość incydentów", "Wprowadź ilość incydentów:", 0, 0, 100)
        if ok_pressed:
            self.data_storage.incidents_count = incidents_count

    def get_position_in_race(self):
        position_in_race, ok_pressed = QInputDialog.getInt(self, "Pozycja w wyścigu", "Wprowadź pozycję w wyniku:", 1, 1, 100)
        if ok_pressed:
            self.data_storage.position_in_race = position_in_race

    def get_track_name(self):
        track_name, ok_pressed = QInputDialog.getText(self, "Tor", "Wprowadź nazwę toru:")
        if ok_pressed and track_name:
            self.data_storage.track_name = track_name

    def save_and_close(self):
        result = RaceResult(
            car_model=self.data_storage.car_model,
            incidents_count=self.data_storage.incidents_count,
            position_in_race=self.data_storage.position_in_race,
            track_name=self.data_storage.track_name
        )
        self.data_storage.add_result_to_history(result)

        self.showStatsSignal.emit()

        self.accept()


class IRacingRaceResult:
    def __init__(self, race_data):
        self.series_name = race_data.get('series_name', '')
        self.car_model = race_data.get('car_model', '')
        self.start_position = race_data.get('start_position', 0)
        self.finish_position = race_data.get('finish_position', 0)
        self.track_name = race_data.get('track_name', '')
        self.incidents_count = race_data.get('incidents_count', 0)
        self.points = race_data.get('points', 0)
        self.strength_of_field = race_data.get('strength_of_field', 0)
        self.qualifying_time = race_data.get('qualifying_time', '')
        self.laps_led = race_data.get('laps_led', 0)

class IRacingOptionsWindow(QDialog):
    showStatsSignal = Signal()

    def __init__(self, data_storage, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opcje iRacing")

        layout = QVBoxLayout()

        button_stats = QPushButton("Twoje statystyki")
        button_stats.clicked.connect(self.show_stats)
        layout.addWidget(button_stats)

        button_add_results = QPushButton("Nadchodzące wyścigi")
        button_add_results.clicked.connect(self.show_add_results_options)
        layout.addWidget(button_add_results)

        layout.addWidget(QPushButton("Ranking światowy"))

        button_back = QPushButton("Powrót do wyboru gry")
        button_back.clicked.connect(self.accept)
        layout.addWidget(button_back)

        self.data_storage = data_storage

        # Dodajemy kontrolkę do wyświetlania wyników w oknie aplikacji
        self.results_text_edit = QTextEdit(self)
        self.results_text_edit.setReadOnly(True)  # Ustawiamy tylko do odczytu
        layout.addWidget(self.results_text_edit)

        self.setLayout(layout)

        self.showStatsSignal.connect(self.show_stats)

    def show_stats(self):
        try:
            idc = irDataClient(username="f12020@o2.pl", password="Kxn157890-")
            driver_info = idc.stats_member_recent_races(cust_id=819528)

            race_results = [IRacingRaceResult(race_data) for race_data in driver_info['races']]

            # Wyświetlamy wyniki w polu tekstowym
            self.results_text_edit.clear()
            for result in race_results:
                self.results_text_edit.append(f"Series: {result.series_name}")
                self.results_text_edit.append(f"Car Model: {result.car_model}")
                self.results_text_edit.append(f"Start Position: {result.start_position}")
                self.results_text_edit.append(f"Finish Position: {result.finish_position}")
                self.results_text_edit.append(f"Track: {result.track_name}")
                self.results_text_edit.append(f"Incidents: {result.incidents_count}")
                self.results_text_edit.append(f"Points: {result.points}")
                self.results_text_edit.append(f"Strength of Field: {result.strength_of_field}")
                self.results_text_edit.append(f"Qualifying Time: {result.qualifying_time}")
                self.results_text_edit.append(f"Laps Led: {result.laps_led}")
                self.results_text_edit.append("-" * 30)

        except Exception as e:
            print(f"Błąd podczas pobierania informacji o kierowcy: {e}")

    def show_add_results_options(self):
        pass

    def populate_results_table(self):
        pass


class DriverInfoWindow(QDialog):
    def __init__(self, driver_info, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Informacje o kierowcy")

        layout = QVBoxLayout()

        self.driver_info_label = QLabel(f"Informacje o kierowcy: {driver_info}")
        layout.addWidget(self.driver_info_label)

        close_button = QPushButton("Zamknij")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication([])

    main_window = MainWindow()
    main_window.showStatsSignal.connect(main_window.delayed_show_stats)
    main_window.show()

    app.exec()
