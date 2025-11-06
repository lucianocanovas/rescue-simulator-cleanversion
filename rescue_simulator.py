import os
from map_manager import MapManager
from visualization import Visualization
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self, saved_game: str | None = None, saved_turn: int | None = None):
        pygame.init()
        # Pedimos a SDL que centre la ventana en la pantalla cuando la cree.
        # Debe establecerse antes de llamar a set_mode.
        try:
            os.environ.setdefault('SDL_VIDEO_CENTERED', '1')    
        except Exception:
            pass

        # Necesitamos un modo de vídeo inicial para permitir cargar sprites con convert()
        # (algunas plataformas requieren un display activo antes de crear Surfaces).
        try:
            pygame.display.set_mode((800, 800))
        except Exception:
            pass

        # Inicializamos el gestor del mapa con las estrategias por defecto
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())

        # Si se pasó una partida guardada, intentar cargarla ahora (esto puede cambiar width/height)
        if saved_game:
            loaded = self.map_manager.load_game(saved_game, saved_turn if saved_turn is not None else 0)
            if not loaded:
                print(f"[ERROR] No se pudo cargar la partida especificada: {saved_game}. Se inicia nueva partida.")
                self.map_manager.new_game()
        else:
            # Iniciamos una nueva partida y guardamos el turno 0
            self.map_manager.new_game()
            try:
                self.map_manager.save_game(0)
            except Exception:
                pass

        # Calculamos un cell_size que permita que el mapa ocupe la mayor parte posible
        # de la pantalla del usuario, dejando un pequeño margen para barras de sistema.
        try:
            info = pygame.display.Info()
            screen_w, screen_h = info.current_w, info.current_h
            # Dejamos un margen (p. ej. 150px) para barras y bordes
            margin = 150
            usable_w = max(200, screen_w - margin)
            usable_h = max(200, screen_h - margin)
            cell_size = max(6, min(usable_w // self.map_manager.width, usable_h // self.map_manager.height))
            # opcional: limitar tamaño máximo de celda
            cell_size = min(cell_size, 64)
        except Exception:
            # Fallback razonable
            cell_size = 16

        win_w = int(cell_size * self.map_manager.width)
        win_h = int(cell_size * self.map_manager.height)
        pygame.display.set_mode((win_w, win_h))

        # Intento de centrar la ventana de forma más precisa en Windows.
        # En Windows usamos MoveWindow con el HWND proporcionado por SDL.
        try:
            if os.name == 'nt':
                import ctypes
                from ctypes import wintypes

                info = pygame.display.get_wm_info()
                # Dependiendo de la plataforma/SDL, la key puede llamarse 'window' o 'hwnd'
                hwnd = info.get('window') or info.get('hwnd')
                if hwnd:
                    # Obtener el área de trabajo (excluye taskbar) para centrar correctamente
                    SPI_GETWORKAREA = 0x0030
                    rect = wintypes.RECT()
                    ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                    if ok:
                        work_w = rect.right - rect.left
                        work_h = rect.bottom - rect.top
                        x = rect.left + max(0, (work_w - win_w) // 2)
                        y = rect.top + max(0, (work_h - win_h) // 2)
                        # Mover la ventana al centro del área de trabajo
                        ctypes.windll.user32.MoveWindow(hwnd, int(x), int(y), int(win_w), int(win_h), True)
        except Exception:
            # Fall back silencioso: SDL centering o gestor de ventanas decidirá la posición
            pass

        # Inicializamos la visualización pasando el tamaño de celda calculado
        self.visualization = Visualization(self.map_manager, cell_size=cell_size)

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