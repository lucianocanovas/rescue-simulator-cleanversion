from map_manager import MapManager
from visualization import Visualization
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self, saved_game=None):
        pygame.init()
        pygame.display.set_mode((800, 800))
        
        # Inicializamos el gestor del mapa con las estrategias por defecto
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())
        
        if saved_game:
            self.map_manager.load_game(saved_game, 0)  # Cargamos una partida guardada
        else:
            self.map_manager.new_game()  # Iniciamos una nueva partida
            
        # Inicializamos la visualización
        self.visualization = Visualization(self.map_manager)

    def start(self):
        print("Game started!")
        self.visualization.run()

def main():
    # Cargar Partida o Iniciar Nueva
    # Preguntar estrategias
    game = GameEngine()
    game.start()

if __name__ == "__main__":
    main()