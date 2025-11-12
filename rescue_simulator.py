import os
from map_manager import MapManager
from visualization import Visualization, CELL_SIZE
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self, saved_game: str | None = None, saved_turn: int | None = None):
        pygame.init()

        try:
            window_width = 50 * CELL_SIZE
            window_height = 50 * CELL_SIZE
        except Exception:
            window_width = 800
            window_height = 800
        pygame.display.set_mode((window_width, window_height))
        
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())
        initial_turn = 0

        if saved_game:
            loaded = self.map_manager.load_game(saved_game, saved_turn if saved_turn is not None else 0)
            if not loaded:
                print(f"❌ - ERROR LOADING GAME: {saved_game}. STARTING NEW GAME INSTEAD.")
                self.map_manager.new_game()
            else:
                initial_turn = saved_turn if saved_turn is not None else 0
                print(f"✅ - LOADED GAME: {saved_game} AT TURN {initial_turn}.")
        else:
            self.map_manager.new_game()
            try:
                self.map_manager.save_game(0)
            except Exception:
                pass

        self.visualization = Visualization(self.map_manager)
        self.visualization.current_turn = initial_turn

    def start(self):
        self.visualization.run()

def main():
    print("=== RESCUE SIMULATOR ===")
    print("NEW GAME OR LOAD SAVED GAME?")
    print("  [N] - NEW GAME")
    print("  [L] - LOAD SAVED GAME")
    choice = input("SELECT [N/L]: ").strip().lower()

    selected_path = None
    selected_turn = None

    if choice in ['l', 'load']:
        base_directory = 'saved_games'
        if not os.path.exists(base_directory):
            print("❗ - NO SAVED GAMES FOUND. STARTING NEW GAME INSTEAD.")
            choice = 'n'
        else:
            saved_games = [directory for directory in os.listdir(base_directory) if directory.startswith('Game_')]
            saved_games.sort(key=lambda x: int(x.split('_')[1]))
            if not saved_games:
                print("❗- NOT SAVED GAMES FOUND. STARTING NEW GAME INSTEAD.")
                choice = 'n'
            else:
                print("AVAILABLE SAVED GAMES:")
                for index, game in enumerate(saved_games):
                    print(f"  {index}: {game}")
                selection = input(f"SELECT GAME INDEX [0-{len(saved_games)-1}] (ENTER to cancel): ").strip()
                if selection == '':
                    print("CANCELLED. STARTING NEW GAME INSTEAD.")
                    choice = 'n'
                else:
                    try:
                        game_index = int(selection)
                        if game_index < 0 or game_index >= len(saved_games):
                            raise ValueError()
                        selected_folder = os.path.join(base_directory, saved_games[game_index])
                        turn_files = [file for file in os.listdir(selected_folder) if file.startswith('turn_') and file.endswith('.pkl')]
                        turn_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
                        if not turn_files:
                            print("❗- NO TURNS FOUND IN SELECTED GAME. STARTING NEW GAME INSTEAD.")
                            choice = 'n'
                        else:
                            print("AVAILABLE TURNS:")
                            for turn_index, turn_file in enumerate(turn_files):
                                print(f"  {turn_index}: {turn_file}")
                            turn_selection = input(f"SELECT TURN INDEX [0-{len(turn_files)-1}] (ENTER for last turn): ").strip()
                            if turn_selection == '':
                                turn_file_index = len(turn_files) - 1
                            else:
                                turn_file_index = int(turn_selection)
                            selected_path = os.path.join(selected_folder, turn_files[turn_file_index])
                            try:
                                selected_turn = int(turn_files[turn_file_index].split('_')[1].split('.')[0])
                            except Exception:
                                selected_turn = None
                    except Exception:
                        print("❗- INVALID SELECTION. STARTING NEW GAME INSTEAD.")
                        choice = 'n'

    if choice == 'n' or choice == '' or choice is None:
        engine = GameEngine()
    else:
        engine = GameEngine(saved_game=selected_path, saved_turn=selected_turn)
    engine.start()

if __name__ == "__main__":
    main()