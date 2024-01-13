from PySide6.QtCore import Signal, QTimer, QObject, Qt, QDateTime
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QTableWidget, \
    QTableWidgetItem, QLabel, QTextEdit, QHeaderView, QLineEdit, QMessageBox, QSpinBox
from PySide6.QtGui import QFont
import pytz
import pandas as pd
import sqlite3
import keyring
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
        self.conn = sqlite3.connect("data.db")
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                car_model TEXT,
                incidents_count INTEGER,
                position_in_race INTEGER,
                track_name TEXT
            )
        ''')
        self.conn.commit()

    def load_from_database(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM results')
        rows = cursor.fetchall()
        self.results_history = [
            RaceResult(car_model=row[0], incidents_count=row[1], position_in_race=row[2], track_name=row[3]) for row in rows
        ]

    def save_to_database(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM results')
        for result in self.results_history:
            cursor.execute('''
                INSERT INTO results (car_model, incidents_count, position_in_race, track_name)
                VALUES (?, ?, ?, ?)
            ''', (result.car_model, result.incidents_count, result.position_in_race, result.track_name))
        self.conn.commit()

    def add_result_to_history(self, result):
        self.results_history.insert(0, result)
        self.results_history = self.results_history[:self.max_results_history]
        self.save_to_database()

class MainWindow(QWidget):
    showStatsSignal = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Wybierz grę")
        self.setFixedSize(250, 100)
        layout = QVBoxLayout()

        button_project_cars = QPushButton("Project Cars 2")
        button_project_cars.clicked.connect(lambda: self.show_game_options("Project Cars 2"))
        layout.addWidget(button_project_cars)

        button_iracing = QPushButton("iRacing")
        button_iracing.clicked.connect(lambda: self.show_game_options("iRacing"))
        layout.addWidget(button_iracing)

        self.data_storage = DataStorage()
        self.data_storage.load_from_database()
        self.setLayout(layout)
        font = QFont("Calibri", 15)
        self.setFont(font)

    def show_game_options(self, game_name):
        if game_name == "Project Cars 2":
            project_cars_options_window = ProjectCarsOptionsWindow(self.data_storage, self)
            project_cars_options_window.showStatsSignal.connect(project_cars_options_window.populate_results_table)
            project_cars_options_window.showStatsSignal.connect(project_cars_options_window.show_stats)
            project_cars_options_window.exec()
        elif game_name == "iRacing":
            iracing_options_window = IRacingOptionsWindow(self.data_storage, self)
            iracing_options_window.showStatsSignal.connect(iracing_options_window.show_stats)
            iracing_options_window.exec()

        self.close

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
        self.data_storage.load_from_database()
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

class ProjectCarsOptionsWindow(QDialog):
    showStatsSignal = Signal()

    def __init__(self, data_storage, parent=None):
        super().__init__(parent)
        font = QFont("Calibri", 15)
        self.setFont(font)
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
        font = QFont("Calibri", 15)
        self.setFont(font)
        layout = QVBoxLayout()

        self.track_name_lineedit = QLineEdit(self)
        self.track_name_lineedit.setPlaceholderText("Wprowadź nazwę toru")
        layout.addWidget(self.track_name_lineedit)
        self.incidents_count_spinbox = QSpinBox(self)
        self.incidents_count_spinbox.setPrefix("Ilość incydentów: ")
        self.incidents_count_spinbox.setMinimum(0)
        layout.addWidget(self.incidents_count_spinbox)
        self.position_in_race_spinbox = QSpinBox(self)
        self.position_in_race_spinbox.setPrefix("Pozycja w wyścigu: ")
        self.position_in_race_spinbox.setMinimum(1)
        layout.addWidget(self.position_in_race_spinbox)
        self.car_model_lineedit = QLineEdit(self)
        self.car_model_lineedit.setPlaceholderText("Wprowadź nazwę auta")
        layout.addWidget(self.car_model_lineedit)
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)
        back_button = QPushButton("Powrót do opcji Project Cars 2")
        back_button.clicked.connect(self.accept)
        layout.addWidget(back_button)

        self.data_storage = data_storage
        self.data_storage.load_from_database()
        self.setLayout(layout)

    def save_and_close(self):
        track_name = self.track_name_lineedit.text()
        car_model = self.car_model_lineedit.text()
        incidents_count = self.incidents_count_spinbox.value()
        position_in_race = self.position_in_race_spinbox.value()

        if track_name and car_model:
            result = RaceResult(
                car_model=car_model,
                incidents_count=incidents_count,
                position_in_race=position_in_race,
                track_name=track_name
            )
            self.data_storage.add_result_to_history(result)
            self.data_storage.save_to_database()
            self.showStatsSignal.emit()
            self.accept()
        else:
            QMessageBox.warning(
                self, "Brak wymaganych informacji", "Wprowadź wszystkie wymagane informacje."
            )
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
        169:"Porsche 911 GT3 R (992)",
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

    series_id_to_name = {
        32: "Advanced Legends Cup",
        33: "iRacing Late Model Tour",
        34: "Skip Barber Race Series",
        45: "SK Modified Weekly Series",
        47: "NASCAR iRacing Class C",
        53: "Silver Crown Cup",
        58: "NASCAR Class A",
        62: "NASCAR iRacing Class B",
        63: "Spec Racer Ford Challenge",
        65: "Classic Lotus Grand Prix",
        74: "Radical Esports Cup",
        102: "NASCAR Tour Modified Series",
        103: "NASCAR Class B Fixed Setup",
        112: "Production Car Sim-Lab Challenge",
        116: "Carburetor Cup",
        131: "Sprint Car Cup",
        133: "US Open Wheel B - Dallara IR-18",
        139: "Global Mazda MX-5 Fanatec Cup",
        164: "NASCAR Class C Maconi Setup Shop Fixed",
        165: "US Open Wheel C - Dallara IR18 Fixed Series",
        167: "ARCA Menards Series",
        182: "Street Stock Fanatec Series - R",
        190: "Street Stock Next Level Racing Series - C",
        191: "NASCAR Class A Fixed",
        201: "Grand Prix Legends",
        210: "Global Fanatec Challenge",
        223: "Super Late Model Series",
        228: "GT Sprint VRS Series",
        231: "Advanced Mazda MX-5 Cup Series",
        237: "GT Endurance VRS Series",
        259: "PickUp Cup",
        260: "Formula A - Grand Prix Series",
        285: "IMSA Vintage Series",
        291: "DIRTcar Limited Late Model Series",
        292: "DIRTcar 305 Sprint Car Fanatec Series",
        299: "iRacing Porsche Cup",
        305: "DIRTcar 360 Sprint Car Carquest Series",
        306: "DIRTcar Pro Late Model Series",
        307: "World of Outlaws Sprint Car Series",
        308: "World of Outlaws Late Model Series",
        309: "AMSOIL USAC Sprint Car - Fixed",
        310: "USAC 360 Sprint Car Series",
        311: "DIRTcar Class C Street Stock Series - Fixed",
        315: "Dirt Legends Cup",
        325: "Rallycross Series",
        327: "Dirt Midget Cup",
        353: "Ferrari GT3 Challenge - Fixed",
        359: "Formula B - Formula Renault 3.5 Series",
        369: "World of Outlaws Late Model Series - Fixed",
        391: "Pro 4 Off Road Racing Series",
        399: "Supercars Series",
        405: "Supercars Series - Australian Server Only",
        413: "NASCAR Legends Series",
        414: "US Open Wheel C - Indy Pro 2000 Series",
        416: "Super Late Model Series - Fixed",
        417: "NASCAR Tour Modified Series - Fixed",
        419: "IMSA Endurance Series",
        428: "SUPER DIRTcar Big Block Modified Series",
        429: "Dallara Formula iR - Fixed",
        430: "Touring Car Challenge - Fixed",
        431: "Formula C - DOF Reality Dallara F3 Series",
        432: "Proto-GT Thrustmaster Challenge",
        440: "CARS Late Model Stock Toyr - Fixed",
        441: "SK Modified Weekly Series - Fixed",
        442: "DIRTcar UMP Modified Series - Fixed",
        443: "US Open Wheel D - USF 2000 Series - Fixed",
        444: "GT3 Fanatec Challenge - Fixed",
        446: "Rookie DIRTcar Street Stock Series - Fixed",
        447: "IMSA iRacing Series",
        455: "Formula Vee SIMAGIC Series",
        456: "Formula C - Thrustmaster Dallara F3 Series - Fixed",
        457: "LMP2 Prototype Challenge Fixed",
        458: "World of Outlaws Sprint Car Series - Fixed",
        459: "Rookie IRX Volkswagen Beetle Lite - Fixed",
        460: "iRX Volkswagen Beetle Lite",
        461: "Rallycross Series - Fixed",
        462: "Rookie Pro 2 Lite Off-Road Racing Series - Fixed",
        463: "Pro 4 Off-Road Racing Series - Fixed",
        464: "Pro 2 Off-Road Racing Series - Fixed",
        466: "DIRTcar 358 Modified Engine Ice Series",
        471: "Dallara Dash",
        476: "iRacing Porsche Cup - Fixed",
        481: "Winter iRacing Nascar Series - Fixed",
        482: "Winter iRacing Nascar Series",
        483: "Rookie Legends VRS Cup",
        484: "Formula A - Grand Prix Series - Fixed",
        490: "Pro 2 Off-Road Racing Series",
        491: "GT4 Falken Tyre Challenge-Fixed",
        492: "IMSA Michelin Pilot Challenge",
        493: "Stock Car Brasil - Fixed",
        497: "FIA Formula 4 Challenge",
        498: "FIA Formula 4 Challenge - Fixed",
        500: "Dirt Super Late Model Tour - Fixed",
        501: "Dirt 410 Sprint Car Tour",
        502: "Falken Tyre Sports Car Challenge",
        503: "Touring Car Challenge",
        505: "Mission R Challenge - Fixed",
        514: "GR Buttkicker Cup - Fixed",
        515: "Dirt Car 360 Sprint Fixed",
        516: "Dirt Midget Cup Fixed",
        517: "DIRTcar Pro Late Model Series - Fixed",
        518: "SUPER DIRTcar Big Block Modifieds Series - Fixed",
        519: "Clio Cup - Fixed",
        520: "Formula 1600 Rookie Sim-Motion Series - Fixed",
        521: "Formula 1600 Thrustmaster Trophy",
        524: "Gen 4 Cup - Fixed",
        525: "LMP3 Turn Racing Trophy - Fixed",
        526: "Ring Meister Ricmotech Series - Fixed",
        530: "Mustang Skip Barber Challenge - Fixed",
        535: "GTE Sprint Pure Driving School Series",
        536: "Formula B - Super Formula IMSIM Series",
        537: "Formula B - Super Formula IMSIM Series - Fixed",
        538: "Draft Master - Fixed",
        539: "IMSA iRacing Series - Fixed",
        540: "FIA F4 Esports Regional Tour - America",
        541: "FIA F4 Esports Regional Tour - East",
        542: "FIA F4 Esports Regional Tour - South",
        543: "FIA F4 Esports Regional Tour - North",
        548: "Weekly Race Challenge",
        
        }
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
        self.username = ""
        self.password = ""
        self.load_credentials()
        
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

        self.current_time_label = QLabel("", alignment=Qt.AlignCenter)
        self.layout.addWidget(self.current_time_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_current_time)
        self.timer.start(1000)
        self.last_api_update_time = QDateTime.currentDateTime()
        

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

            df = pd.read_csv(r'C:\\Users\\kbuga\\OneDrive\\Pulpit\\EiT 3 SEMESTR\\_repos\\projekt-programowanie-Buglix\\Simracing Data App\\Road_driver_stats.csv')
            top_30_drivers = df.head(30)
            for index, row in top_30_drivers.iterrows():
                driver = row['DRIVER']
                irating = row['IRATING']
                avg_incidents = row['AVG_INC']
                avg_finish = row['AVG_FINISH_POS']
                self.world_ranking_text_edit.append(f"IRating: {irating}")
                self.world_ranking_text_edit.append(f"Driver Name: {driver}")
                self.world_ranking_text_edit.append(f"Average incidents: {avg_incidents}")
                self.world_ranking_text_edit.append(f"Average finish position: {avg_finish}")
                self.world_ranking_text_edit.append("-" * 30)
        except Exception as e:
            print(f"Błąd podczas wczytywania informacji o rankingu światowym z pliku CSV: {e}")
    
        self.world_ranking_text_edit.show()
        self.stats_text_edit.hide()
        self.upcoming_races_label.hide()
        self.world_ranking_text_edit.verticalScrollBar().setValue(0)
        self.adjustSize()
    def show_stats(self):
            if not self.username or not self.password:
                self.prompt_for_credentials()
                return
            try:
                idc = irDataClient(username=self.username, password=self.password)
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

    def show_upcoming_races(self):
            if not self.username or not self.password:
                self.prompt_for_credentials()
                return
            try:
                idc = irDataClient(username=self.username, password=self.password)
                upcoming_races_info = idc.season_race_guide()

                for race_info in upcoming_races_info['sessions']:

                    series_name1 = self.series_id_to_name.get(race_info['series_id'], "Nieznane")

                    start_time_str = race_info['start_time']
                    start_time_utc = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    start_time_local = start_time_utc.astimezone(pytz.timezone('Europe/Warsaw'))
                    start_time_str_local = start_time_local.strftime("%Y-%m-%d %H:%M:%S")
                    end_time_str = race_info['end_time']
                    end_time_utc = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    end_time_local = end_time_utc.astimezone(pytz.timezone('Europe/Warsaw'))
                    end_time_str_local = end_time_local.strftime("%Y-%m-%d %H:%M:%S")

                    self.upcoming_races_text_edit.append(f"Race week number: {race_info['race_week_num'] + 1}")
                    self.upcoming_races_text_edit.append(f"Start Time: {start_time_str_local}")
                    self.upcoming_races_text_edit.append(f"End Time: {end_time_str_local}")
                    self.upcoming_races_text_edit.append(f"Series name: {series_name1}")
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
    
    def update_current_time(self):
        current_time_utc = QDateTime.currentDateTimeUtc()
        current_time_gmt_plus_one = current_time_utc.addSecs(3600)
        current_time_str = current_time_gmt_plus_one.toString("yyyy-MM-dd HH:mm:ss")

        elapsed_seconds = self.last_api_update_time.secsTo(current_time_utc)
        if elapsed_seconds >= 0:
            self.upcoming_races_label.setText(f"Aktualny czas: {current_time_str}")
            self.upcoming_races_label.setAlignment(Qt.AlignCenter)

    def start_timer(self):
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    def load_credentials(self):
        self.username = keyring.get_password("SimracingDataApp", "iRacingUsername")
        self.password = keyring.get_password("SimracingDataApp", "iRacingPassword")
    
    def save_credentials(self):
        keyring.set_password("SimracingDataApp", "iRacingUsername", self.username)
        keyring.set_password("SimracingDataApp", "iRacingPassword", self.password)
    
    def prompt_for_credentials(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec() == QDialog.Accepted:
            self.username, self.password = login_dialog.get_credentials()
            self.save_credentials()
            self.show_stats()
class MyApp:
    def clear_credentials(self):
        try:
            keyring.delete_password('SimracingDataApp', 'iRacingUsername')
            keyring.delete_password('SimracingDataApp', 'iRacingPassword')
            print("Dane logowania wyczyszczone.")
        except keyring.errors.PasswordDeleteError as e:
            print("Dane logowania nie zostały podane.")

    def closeEvent(self, event):
        self.clear_credentials()
        event.accept()
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Logowanie do iRacing API")

        layout = QVBoxLayout()

        self.username_lineedit = QLineEdit(self)
        self.username_lineedit.setPlaceholderText("Nazwa użytkownika")
        layout.addWidget(self.username_lineedit)

        self.password_lineedit = QLineEdit(self)
        self.password_lineedit.setPlaceholderText("Hasło")
        self.password_lineedit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_lineedit)

        login_button = QPushButton("Zaloguj")
        login_button.clicked.connect(self.accept)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def get_credentials(self):
        username = self.username_lineedit.text()
        password = self.password_lineedit.text()
        return username, password
        
if __name__ == "__main__":
    app = QApplication([])

    main_window = MainWindow()
    main_window.show()

    my_app = MyApp()
    app.aboutToQuit.connect(my_app.clear_credentials)

    app.exec()