import os
from map_manager import MapManager
from visualization import Visualization, CELL_SIZE
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self, saved_game: str | None = None, saved_turn: int | None = None):
        pygame.init()

        # Window size setup
        try:
            win_w = 50 * CELL_SIZE
            win_h = 50 * CELL_SIZE
        except Exception:
            win_w = 800
            win_h = 800
        pygame.display.set_mode((win_w, win_h))
        
        # MapManager initialization
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())
        initial_turn = 0

        if saved_game:
            # Try to load the saved game
            loaded = self.map_manager.load_game(saved_game, saved_turn if saved_turn is not None else 0)
            if not loaded:
                print(f"❌ - ERROR LOADING GAME: {saved_game}. STARTING NEW GAME INSTEAD.")
                self.map_manager.new_game()
            else:
                # Si la carga fue exitosa, usar el turno especificado
                initial_turn = saved_turn if saved_turn is not None else 0
                print(f"✅ - LOADED GAME: {saved_game} AT TURN {initial_turn}.")
        else:
            # Start a new game
            self.map_manager.new_game()
            try:
                self.map_manager.save_game(0)
            except Exception:
                pass

        # Visualization setup
        self.visualization = Visualization(self.map_manager)
        self.visualization.current_turn = initial_turn

    def start(self):
        self.visualization.run()

def main():
    # Ask user to start new game or load saved game
    print("=== RESCUE SIMULATOR ===")
    print("NEW GAME OR LOAD SAVED GAME?")
    print("  [N] - NEW GAME")
    print("  [L] - LOAD SAVED GAME")
    choice = input("SELECT [N/L]: ").strip().lower()

    selected_path = None
    selected_turn = None

    if choice == 'L' or choice == 'load' or choice == 'l':
        base_dir = 'saved_games'
        if not os.path.exists(base_dir):
            print("❗ - NO SAVED GAMES FOUND. STARTING NEW GAME INSTEAD.")
            choice = 'n'
        else:
            partidas = [d for d in os.listdir(base_dir) if d.startswith('Partida_')]
            partidas.sort(key=lambda x: int(x.split('_')[1]))
            if not partidas:
                print("❗- NOT SAVED GAMES FOUND. STARTING NEW GAME INSTEAD.")
                choice = 'n'
            else:
                print("AVAILABLE SAVED GAMES:")
                for i, p in enumerate(partidas):
                    print(f"  {i}: {p}")
                sel = input(f"SELECT GAME INDEX [0-{len(partidas)-1}] (ENTER to cancel): ").strip()
                if sel == '':
                    print("CANCELLED. STARTING NEW GAME INSTEAD.")
                    choice = 'n'
                else:
                    try:
                        index = int(sel)
                        if index < 0 or index >= len(partidas):
                            raise ValueError()
                        sel_folder = os.path.join(base_dir, partidas[index])
                        # listar turnos disponibles
                        turno_files = [f for f in os.listdir(sel_folder) if f.startswith('turno_') and f.endswith('.pkl')]
                        # Ordenar numéricamente por el número de turno
                        turno_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
                        if not turno_files:
                            print("❗- NO TURNS FOUND IN SELECTED GAME. STARTING NEW GAME INSTEAD.")
                            choice = 'n'
                        else:
                            print("AVAILABLE TURNS:")
                            for j, tf in enumerate(turno_files):
                                print(f"  {j}: {tf}")
                            sel2 = input(f"SELECT TURN INDEX [0-{len(turno_files)-1}] (ENTER for last turn): ").strip()
                            if sel2 == '':
                                sel2_index = len(turno_files) - 1
                            else:
                                sel2_index = int(sel2)
                            selected_path = os.path.join(sel_folder, turno_files[sel2_index])
                            # Extract turn number from filename if possible
                            try:
                                selected_turn = int(turno_files[sel2_index].split('_')[1].split('.')[0])
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