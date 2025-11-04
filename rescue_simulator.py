from map_manager import MapManager
from visualization import Visualization
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self, saved_game=None):
        pygame.init()
        # Ajustamos la ventana al tamaño del mapa (ancho x alto) usando CELL_SIZE de visualization
        # Importamos Visualization's CELL_SIZE indirectamente: asumimos 16 por defecto si no está disponible
        try:
            from visualization import CELL_SIZE
            win_w = 50 * CELL_SIZE
            win_h = 50 * CELL_SIZE
        except Exception:
            win_w = 800
            win_h = 800
        pygame.display.set_mode((win_w, win_h))
        
        # Inicializamos el gestor del mapa con las estrategias por defecto
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())
        
        if saved_game:
            self.map_manager.load_game(saved_game, 0)  # Cargamos una partida guardada
        else:
            self.map_manager.new_game()  # Iniciamos una nueva partida
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
    # Cargar Partida o Iniciar Nueva
    # Preguntar estrategias
    game = GameEngine()
    game.start()

if __name__ == "__main__":
    main()