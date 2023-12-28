from PySide6.QtCore import Signal, QTimer, QObject, Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QTableWidget, \
    QTableWidgetItem, QInputDialog, QLabel, QTextEdit, QHeaderView

import pytz
import pandas as pd
import json
from iracingdataapi.client import irDataClient
from datetime import datetime
class SignalHandler(QObject):
    showStatsSignal = Signal()

class RaceResult:
    def __init__(self, *args, **kwargs):
        self.car_model = kwargs.get("car_model", "")
        self.incidents_count = kwargs.get("incidents_count", 0)
        self.position_in_race = kwargs.get("position_in_race", 0)
        self.track_name = kwargs.get("track_name", "")


class DataStorage:
    def __init__(self):
        self.car_model = None
        self.incidents_count = None
        self.position_in_race = None
        self.track_name = None
        self.results_history = []  
        self.max_results_history = 15
    
    def load_from_file(self):
        try:
            with open("data.json", "r") as file:
                data = json.load(file) 
            self.car_model = data.get("car_model")
            self.incidents_count = data.get("incidents_count")
            self.position_in_race = data.get("position_in_race")
            self.track_name = data.get("track_name")
            self.results_history = [
                RaceResult(**result) for result in data.get("results_history", [])
            ]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Błąd podczas wczytywania danych z pliku: {e}")

    def save_to_file(self):
        data = {
            "car_model": self.car_model,
            "incidents_count": self.incidents_count,
            "position_in_race": self.position_in_race,
            "track_name": self.track_name,
            "results_history": [
                {
                    "car_model": result.car_model,
                    "incidents_count": result.incidents_count,
                    "position_in_race": result.position_in_race,
                    "track_name": result.track_name
                } for result in self.results_history
            ]
        }
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)

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
        self.data_storage.load_from_file()
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

            self.showStatsSignal.connect(lambda: iracing_options_window.show())
            
            iracing_options_window.hide()
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
        self.setFixedSize(555, 500)

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
        
        self.results_table.resizeColumnsToContents()
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

class IRacingStatsWindow(StatsWindow):
    def __init__(self, results_history, parent=None):
        super().__init__(results_history, parent)

    def populate_results_table(self, results_history):
        for result in reversed(results_history):
            rowPosition = self.results_table.rowCount()
            self.results_table.insertRow(rowPosition)
            self.results_table.setItem(rowPosition, 0, QTableWidgetItem(IRacingRaceResult.car_id_to_car_name.get(result.car_id, "Unknown")))
            self.results_table.setItem(rowPosition, 1, QTableWidgetItem(str(result.incidents_count)))
            self.results_table.setItem(rowPosition, 2, QTableWidgetItem(str(result.start_position)))
            self.results_table.setItem(rowPosition, 3, QTableWidgetItem(str(result.finish_position)))
            self.results_table.setItem(rowPosition, 4, QTableWidgetItem(result.track_name))



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

        button_back = QPushButton("Powrót do wyboru gry")
        button_back.clicked.connect(self.accept)
        layout.addWidget(button_back)

        self.results_table = None
        self.data_storage = data_storage  

        self.setLayout(layout)

    def show_stats(self):
        stats_window = StatsWindow(self.data_storage.results_history, self)
        stats_window.exec()

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
        self.results_table.resizeColumnsToContents()

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
        self.setFixedSize(593, 675)

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
        position_in_race, ok_pressed = QInputDialog.getInt(self, "Pozycja w wyścigu", "Wprowadź pozycję w wyścigu:", 1, 1, 100)
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
        self.data_storage.save_to_file()
        
        self.showStatsSignal.emit()
        
        self.accept()
class IRacingRaceResult:

    car_id_to_car_name = {
        1:"Skip Barber Formula 2000",
        2:"Modified - SK",
        3:"Pontiac Solstice",
        4:"[Legacy] Pro Mazda",
        5:"Legends Ford '34 Coupe",
        10:"Pontiac Solstice - Rookie",
        11:"Legends Ford '34 Coupe - Rookie",
        12:"[Retired] - Chevrolet Monte Carlo SS",
        13:"Radical SR8",
        18:"Silver Crown",
        20:"[Legacy] NASCAR Truck Chevrolet Silverado - 2008",
        21:"[Legacy] Riley MkXX Daytona Prototype - 2008",
        22:"[Legacy] NASCAR Cup Chevrolet Impala COT - 2009",
        23:"SCCA Spec Racer Ford",
        24:"ARCA Menards Chevrolet Impala",
        25:"Lotus 79",
        26:"Chevrolet Corvette C6.R GT1",
        27:"VW Jetta TDI Cup",
        28:"[Legacy] V8 Supercar Ford Falcon - 2009",
        29:"[Legacy] Dallara IR-05",
        30:"Ford Mustang FR500S",
        31:"Modified - NASCAR Whelen Tour",
        33:"Williams-Toyota FW31",
        34:"[Legacy] Mazda MX-5 Cup - 2010",
        35:"[Legacy] Mazda MX-5 Roadster - 2010",
        36:"Street Stock",
        37:"Sprint Car",
        38:"[Legacy] NASCAR Nationwide Chevrolet Impala - 2012",
        39:"HPD ARX-01c",
        41:"Cadillac CTS-V Racecar",
        43:"McLaren MP4-12C GT3",
        44:"Kia Optima",
        59:"Ford GT GT3",
        67:"Global Mazda MX-5 Cup",
        128:"Dallara P217",
        132:"BMW M4 GT3",
        148:"FIA F4",
        157:"Mercedes-AMG GT4",
        159:"BMW M Hybrid V8",
        160:"Toyota GR86",
        173:"Ferrari 296 GT3",
        176:"Audi R8 LMS EVO II GT3",
    }
    def __init__(self, race_data):
        self.series_name = race_data.get('series_name', '')
        self.start_position = race_data.get('start_position', 0)
        self.finish_position = race_data.get('finish_position', 0)
        self.track_name = race_data.get('track', {}).get('track_name', '')
        self.incidents_count = race_data.get('incidents', 0)
        self.points = race_data.get('points', 0)
        self.strength_of_field = race_data.get('strength_of_field', 0)
        self.oldi_rating = race_data.get('oldi_rating', '')
        self.newi_rating = race_data.get('newi_rating', '')
        self.laps_led = race_data.get('laps_led', 0)
        self.car_id = race_data.get('car_id', 0)
        self.car_name = IRacingRaceResult.car_id_to_car_name.get(self.car_id, 'Unknown')
    

class IRacingOptionsWindow(QDialog):
    showStatsSignal = Signal()
    showWorldRankingSignal = Signal()
    showUpcomingRacesSignal = Signal()

    def __init__(self, data_storage, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opcje iRacing")

        self.layout = QVBoxLayout(self)

        self.button_stats = QPushButton("Twoje statystyki")
        self.button_stats.clicked.connect(self.show_stats)
        self.layout.addWidget(self.button_stats)

        self.button_upcoming_races = QPushButton("Nadchodzące wyścigi")
        self.button_upcoming_races.clicked.connect(self.show_upcoming_races)
        self.layout.addWidget(self.button_upcoming_races)

        self.button_ranking = QPushButton("Ranking światowy")
        self.button_ranking.clicked.connect(self.show_world_ranking)
        self.layout.addWidget(self.button_ranking)

        self.button_back = QPushButton("Powrót do wyboru gry")
        self.button_back.clicked.connect(self.accept)
        self.layout.addWidget(self.button_back)

        self.data_storage = data_storage

        self.upcoming_races_label = QLabel("", alignment=Qt.AlignCenter)
        self.layout.addWidget(self.upcoming_races_label)
        
        self.stats_text_edit = QTextEdit(self)
        self.stats_text_edit.setReadOnly(True)
        self.layout.addWidget(self.stats_text_edit)
        self.stats_text_edit.hide()

        self.world_ranking_text_edit = QTextEdit(self)
        self.world_ranking_text_edit.setReadOnly(True)
        self.layout.addWidget(self.world_ranking_text_edit)
        self.world_ranking_text_edit.hide()

        self.showWorldRankingSignal.connect(self.show_world_ranking_table)

        self.showStatsSignal.connect(self.show_stats)

        self.upcoming_races_text_edit = QTextEdit()
        self.upcoming_races_text_edit.setReadOnly(True)
        self.layout.addWidget(self.upcoming_races_text_edit)
        self.upcoming_races_text_edit.hide()

        self.showUpcomingRacesSignal.connect(self.show_upcoming_races)
        

    def show_world_ranking(self):
        self.showWorldRankingSignal.emit()

    def show_upcoming_races(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.upcoming_races_label.setText(f"Aktualny czas: {current_time}")

        self.stats_text_edit.hide()
        self.world_ranking_text_edit.hide()

    def show_world_ranking_table(self):
        self.world_ranking_text_edit.clear()

        try:

            df = pd.read_csv(r'C:\\Users\\kbuga\\OneDrive\\Pulpit\\EiT 3 SEMESTR\\_repos\\projekt-programowanie-Buglix\\Aplikacja_1Python\\Road_driver_stats.csv')
            top_30_drivers = df.head(30)
            for index, row in top_30_drivers.iterrows():
                driver = row['DRIVER']
                irating = row['IRATING']
                self.world_ranking_text_edit.append(f"IRating: {irating}")
                self.world_ranking_text_edit.append(f"Driver Name: {driver}")
                self.world_ranking_text_edit.append("-" * 30)
        except Exception as e:
            print(f"Błąd podczas wczytywania informacji o rankingu światowym z pliku CSV: {e}")
    
        self.world_ranking_text_edit.show()
        self.stats_text_edit.hide()
        self.upcoming_races_label.hide()
        self.world_ranking_text_edit.verticalScrollBar().setValue(0)
        self.adjustSize()
    def show_stats(self):
        if not self.stats_text_edit.isVisible():
            try:
                idc = irDataClient(username="*", password="*")
                driver_info = idc.stats_member_recent_races(cust_id=819528)
                race_results = [IRacingRaceResult(race_data) for race_data in driver_info['races']]

                for result in race_results:
                    self.stats_text_edit.append(f"Series: {result.series_name}")
                    self.stats_text_edit.append(f"Car Model: {result.car_name}")
                    self.stats_text_edit.append(f"Track: {result.track_name}")
                    self.stats_text_edit.append(f"Start Position: {result.start_position}")
                    self.stats_text_edit.append(f"Finish Position: {result.finish_position}")
                    self.stats_text_edit.append(f"Incidents: {result.incidents_count}")
                    self.stats_text_edit.append(f"Points: {result.points}")
                    self.stats_text_edit.append(f"Strength of Field: {result.strength_of_field}")
                    self.stats_text_edit.append(f"Old rating: {result.oldi_rating}")
                    self.stats_text_edit.append(f"New rating: {result.newi_rating}")
                    self.stats_text_edit.append(f"Laps Led: {result.laps_led}")
                    self.stats_text_edit.append("-" * 30)

            except Exception as e:
                print(f"Błąd podczas pobierania informacji o kierowcy: {e}")
        
            self.stats_text_edit.show()
            self.world_ranking_text_edit.hide()
            self.upcoming_races_label.hide()
            self.stats_text_edit.verticalScrollBar().setValue(0)
            self.adjustSize()

    def show_add_results_options(self):
        pass

    def populate_results_table(self):
        pass

    def show_upcoming_races(self):
        if not self.upcoming_races_text_edit.isVisible():
            try:
                idc = irDataClient(username="*", password="*")
                upcoming_races_info = idc.season_race_guide()

                for race_info in upcoming_races_info['sessions']:

                    start_time_str = race_info['start_time']
                    start_time_utc = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    start_time_local = start_time_utc.astimezone(pytz.timezone('Europe/Warsaw'))
                    start_time_str_local = start_time_local.strftime("%Y-%m-%d %H:%M:%S")
                    end_time_str = race_info['end_time']
                    end_time_utc = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    end_time_local = end_time_utc.astimezone(pytz.timezone('Europe/Warsaw'))
                    end_time_str_local = end_time_local.strftime("%Y-%m-%d %H:%M:%S")

                    self.upcoming_races_text_edit.append(f"Race week number: {race_info['race_week_num']}")
                    self.upcoming_races_text_edit.append(f"Series ID: {race_info['series_id']}")
                    self.upcoming_races_text_edit.append(f"Start Time: {start_time_str_local}")
                    self.upcoming_races_text_edit.append(f"End Time: {end_time_str_local}")
                    self.upcoming_races_text_edit.append(f"Season ID: {race_info['season_id']}")
                    self.upcoming_races_text_edit.append(f"Entry Count: {race_info['entry_count']}")
                    self.upcoming_races_text_edit.append("-" * 30)

            except Exception as e:
                print(f"Błąd podczas pobierania informacji o nadchodzących wyścigach: {e}")
    
            self.upcoming_races_text_edit.show()
            self.stats_text_edit.hide()
            self.world_ranking_text_edit.hide()
            self.upcoming_races_text_edit.verticalScrollBar().setValue(0)
            self.adjustSize()
    def convert_to_local_time(self, time_str):
        time_str = time_str[:-1] + "+0000"
        time_utc = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z")
        time_local = time_utc.astimezone(pytz.timezone('Europe/Warsaw'))
        return time_local.strftime("%Y-%m-%d %H:%M:%S")
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
