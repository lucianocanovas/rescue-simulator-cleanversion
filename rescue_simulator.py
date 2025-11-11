import os
from map_manager import MapManager
from visualization import Visualization, CELL_SIZE
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self, saved_game: str | None = None, saved_turn: int | None = None):
        pygame.init()
        # Ajustamos la ventana al tamaño del mapa (ancho x alto) usando CELL_SIZE de visualization
        # Importamos Visualization's CELL_SIZE indirectamente: asumimos 16 por defecto si no está disponible
        try:
            win_w = 50 * CELL_SIZE
            win_h = 50 * CELL_SIZE
        except Exception:
            win_w = 800
            win_h = 800
        pygame.display.set_mode((win_w, win_h))
        
        # Inicializamos el gestor del mapa con las estrategias por defecto
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())

        if saved_game:
            # Intentamos cargar la partida solicitada en el turno indicado
            loaded = self.map_manager.load_game(saved_game, saved_turn if saved_turn is not None else 0)
            if not loaded:
                print(f"[ERROR] No se pudo cargar la partida especificada: {saved_game}. Se inicia nueva partida.")
                self.map_manager.new_game()
        else:
            # Iniciamos una nueva partida
            self.map_manager.new_game()
            # Guardamos el estado inicial (turno 0) para poder volver al inicio
            try:
                self.map_manager.save_game(0)
            except Exception:
                pass
        # Inicializamos la visualización
        self.visualization = Visualization(self.map_manager)

    def start(self):
        self.visualization.run()

def main():
    # Preguntar al usuario si desea crear una nueva partida o cargar una existente
    print("¿Deseas crear una partida nueva o cargar una partida guardada?")
    print("  N - Nueva partida")
    print("  C - Cargar partida")
    choice = input("Elige [N/C]: ").strip().lower()

    selected_path = None
    selected_turn = None

    if choice == 'c' or choice == 'cargar' or choice == 'l':
        base_dir = 'saved_games'
        if not os.path.exists(base_dir):
            print("No existen partidas guardadas. Se creará una partida nueva.")
            choice = 'n'
        else:
            partidas = [d for d in os.listdir(base_dir) if d.startswith('Partida_')]
            partidas.sort()
            if not partidas:
                print("No se encontraron carpetas de partidas. Se creará una partida nueva.")
                choice = 'n'
            else:
                print("Partidas disponibles:")
                for i, p in enumerate(partidas):
                    print(f"  {i}: {p}")
                sel = input(f"Selecciona índice de Partida [0-{len(partidas)-1}] (o ENTER para cancelar): ").strip()
                if sel == '':
                    print("Carga cancelada. Se iniciará una nueva partida.")
                    choice = 'n'
                else:
                    try:
                        idx = int(sel)
                        if idx < 0 or idx >= len(partidas):
                            raise ValueError()
                        sel_folder = os.path.join(base_dir, partidas[idx])
                        # listar turnos disponibles
                        turno_files = [f for f in os.listdir(sel_folder) if f.startswith('turno_') and f.endswith('.pkl')]
                        turno_files.sort()
                        if not turno_files:
                            print("No hay turnos guardados en esa partida. Se iniciará una nueva partida.")
                            choice = 'n'
                        else:
                            print("Turnos disponibles:")
                            for j, tf in enumerate(turno_files):
                                print(f"  {j}: {tf}")
                            sel2 = input(f"Selecciona índice de turno [0-{len(turno_files)-1}] (ENTER para último): ").strip()
                            if sel2 == '':
                                sel2_idx = len(turno_files) - 1
                            else:
                                sel2_idx = int(sel2)
                            selected_path = os.path.join(sel_folder, turno_files[sel2_idx])
                            # Extract turn number from filename if possible
                            try:
                                selected_turn = int(turno_files[sel2_idx].split('_')[1].split('.')[0])
                            except Exception:
                                selected_turn = None
                    except Exception:
                        print("Selección inválida. Se iniciará una nueva partida.")
                        choice = 'n'

    if choice == 'n' or choice == '' or choice is None:
        engine = GameEngine()
    else:
        engine = GameEngine(saved_game=selected_path, saved_turn=selected_turn)
    engine.start()

if __name__ == "__main__":
    main()