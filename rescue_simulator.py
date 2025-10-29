from map_manager import MapManager
from visualization import Visualization
from strategies import PickNearest, Kamikaze, Escort, Invader
import pygame

class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.display.set_mode((800, 800))
        
        self.map_manager = MapManager(player1_strategy=PickNearest(), player2_strategy=PickNearest())
        self.map_manager.new_game()
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