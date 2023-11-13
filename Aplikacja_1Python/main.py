from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

import sys

def select_game(game_name):
    if game_name == "Project Cars 2":
        show_project_cars_options()
    elif game_name == "iRacing":
        print("Selected game: iRacing")

def show_project_cars_options():
    window.hide()
    project_cars_options_window = QWidget()
    project_cars_options_window.setWindowTitle("Project Cars 2 Options")

    layout = QVBoxLayout()

    # Przycisk "Twoje statystyki"
    button_stats = QPushButton("Twoje statystyki")
    layout.addWidget(button_stats)

    # Przycisk "Dodaj wyniki"
    button_add_results = QPushButton("Dodaj wyniki")
    button_add_results.clicked.connect(show_add_results_options)
    layout.addWidget(button_add_results)

    # Przycisk "Ranking światowy"
    button_leaderboard = QPushButton("Ranking światowy")
    layout.addWidget(button_leaderboard)

    # Przycisk "Powrót do wyboru gry"
    button_back = QPushButton("Powrót do wyboru gry")
    button_back.clicked.connect(lambda: show_main_window(project_cars_options_window))
    layout.addWidget(button_back)

    project_cars_options_window.setLayout(layout)
    project_cars_options_window.show()

def show_main_window(previous_window):
    previous_window.hide()
    window.show()

def show_add_results_options():
    add_results_options_window = QWidget()
    add_results_options_window.setWindowTitle("Opcje Dodaj wyniki")

    layout = QVBoxLayout()

    # Przycisk "Pozycja w wyścigu"
    button_position = QPushButton("Pozycja w wyścigu")
    layout.addWidget(button_position)
    button_position.clicked.connect(lambda: handle_option("Pozycja w wyścigu"))

    # Przycisk "Model auta"
    button_car_model = QPushButton("Model auta")
    layout.addWidget(button_car_model)
    button_car_model.clicked.connect(lambda: handle_option("Model auta"))

    # Przycisk "Ilość incydentów"
    button_incidents = QPushButton("Ilość incydentów")
    layout.addWidget(button_incidents)
    button_incidents.clicked.connect(lambda: handle_option("Ilość incydentów"))

    back_button = QPushButton("Powrót do opcji Project Cars 2")
    back_button.clicked.connect(add_results_options_window.close)
    layout.addWidget(back_button)

    add_results_options_window.setLayout(layout)
    add_results_options_window.show()

def handle_option(option):
    print(f"Wybrana opcja: {option}")

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Select a Racing Game")

layout = QVBoxLayout()

# Przycisk "Project Cars 2"
button_project_cars = QPushButton("Project Cars 2")
button_project_cars.clicked.connect(lambda: select_game("Project Cars 2"))
layout.addWidget(button_project_cars)

# Przycisk "iRacing"
button_iracing = QPushButton("iRacing")
button_iracing.clicked.connect(lambda: select_game("iRacing"))
layout.addWidget(button_iracing)

window.setLayout(layout)
window.show()

app.exec()


