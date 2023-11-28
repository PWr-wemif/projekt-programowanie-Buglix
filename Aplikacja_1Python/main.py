from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QInputDialog, QMessageBox
import sys
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select a Racing Game")

        layout = QVBoxLayout()

        # Przycisk "Project Cars 2"
        button_project_cars = QPushButton("Project Cars 2")
        button_project_cars.clicked.connect(lambda: self.show_game_options("Project Cars 2"))
        layout.addWidget(button_project_cars)

        # Przycisk "iRacing"
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

        # Przycisk "Twoje statystyki"
        button_stats = QPushButton("Twoje statystyki")
        button_stats.clicked.connect(self.show_stats)
        layout.addWidget(button_stats)

        # Przycisk "Dodaj wyniki"
        button_add_results = QPushButton("Dodaj wyniki")
        button_add_results.clicked.connect(self.show_add_results_options)
        layout.addWidget(button_add_results)

        # Przycisk "Ranking światowy"
        button_leaderboard = QPushButton("Ranking światowy")
        layout.addWidget(button_leaderboard)

        # Przycisk "Powrót do wyboru gry"
        button_back = QPushButton("Powrót do wyboru gry")
        button_back.clicked.connect(self.accept)
        layout.addWidget(button_back)

        self.setLayout(layout)

        # Przechowywanie wprowadzonego modelu auta
        self.car_model = None

    def show_stats(self):
        if self.car_model:
            QMessageBox.information(self, "Twoje statystyki", f"Model auta: {self.car_model}")

    def show_add_results_options(self):
        add_results_options_window = AddResultsOptionsWindow(self)
        add_results_options_window.exec()

class AddResultsOptionsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opcje Dodaj wyniki")

        layout = QVBoxLayout()

        # Przycisk "Pozycja w wyścigu"
        button_position = QPushButton("Pozycja w wyścigu")
        layout.addWidget(button_position)
        button_position.clicked.connect(lambda: self.handle_option("Pozycja w wyścigu"))

        # Przycisk "Model auta"
        button_car_model = QPushButton("Model auta")
        button_car_model.clicked.connect(self.get_car_model)
        layout.addWidget(button_car_model)

        # Przycisk "Ilość incydentów"
        button_incidents = QPushButton("Ilość incydentów")
        layout.addWidget(button_incidents)
        button_incidents.clicked.connect(lambda: self.handle_option("Ilość incydentów"))

        back_button = QPushButton("Powrót do opcji Project Cars 2")
        back_button.clicked.connect(self.accept)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def handle_option(self, option):
        print(f"Wybrana opcja: {option}")

    def get_car_model(self):
        car_model, ok_pressed = QInputDialog.getText(self, "Model auta", "Wprowadź model auta:")
        if ok_pressed and car_model:
            # Przechowujemy wprowadzony model auta w rodzicu
            parent = self.parent()
            if parent and isinstance(parent, ProjectCarsOptionsWindow):
                parent.car_model = car_model

class IRacingOptionsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("iRacing Options")

        layout = QVBoxLayout()

        # Przycisk "Twoje statystyki"
        button_stats = QPushButton("Twoje statystyki")
        layout.addWidget(button_stats)

        # Przycisk "Dodaj wyniki"
        button_add_results = QPushButton("Dodaj wyniki")
        button_add_results.clicked.connect(self.show_add_results_options)
        layout.addWidget(button_add_results)

        # Przycisk "Ranking światowy"
        layout.addWidget(QPushButton("Ranking światowy"))

        # Przycisk "Powrót do wyboru gry"
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


