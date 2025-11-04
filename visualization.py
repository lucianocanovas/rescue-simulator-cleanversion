import pygame
from map_manager import MapManager
from classes.Mine import Mine

# Constants
WINDOW_SIZE = 800
CELL_SIZE = 16  # 800 / 50 = 16 pixels per cell
ROWS = 50
COLUMNS = 50

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class Visualization:
    def __init__(self, map_manager: MapManager):
        self.map_manager = map_manager
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.current_turn = 0
        self.running = True
        pygame.display.set_caption("Rescue Simulator")
        
    def draw_grid(self):
        for x in range(0, WINDOW_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, WINDOW_SIZE))
        for y in range(0, WINDOW_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (WINDOW_SIZE, y))
    
    def draw_objects(self):
        for x in range(self.map_manager.width):
            for y in range(self.map_manager.height):
                obj = self.map_manager.grid[x][y]
                if isinstance(obj, Mine):
                    radius_x = obj.x_radius * CELL_SIZE
                    radius_y = obj.y_radius * CELL_SIZE
                    center_x = x * CELL_SIZE + CELL_SIZE // 2
                    center_y = y * CELL_SIZE + CELL_SIZE // 2
                    pygame.draw.rect(self.screen, RED, (center_x - radius_x, center_y - radius_y, radius_x * 2, radius_y * 2), 1)
                if obj is not None:
                    pixel_x = x * CELL_SIZE
                    pixel_y = y * CELL_SIZE
                    scaled_sprite = pygame.transform.scale(obj.sprite, (CELL_SIZE, CELL_SIZE))
                    self.screen.blit(scaled_sprite, (pixel_x, pixel_y))
    
    def draw_bases(self):
        # Draw Player 1 Base
        pygame.draw.rect(self.screen, BLUE, (0, 0, CELL_SIZE, CELL_SIZE * self.map_manager.height))
        # Draw Player 2 Base
        pygame.draw.rect(self.screen, RED, (WINDOW_SIZE - CELL_SIZE, 0, CELL_SIZE, CELL_SIZE * self.map_manager.height))

    def draw_player_info(self):
        font = pygame.font.SysFont(None, 40)
        box_w, box_h = 180, 48
        box_x = (WINDOW_SIZE - box_w) // 2
        box_y = (WINDOW_SIZE - box_h)
        pygame.draw.rect(self.screen, (0 ,0 ,0), (box_x - 2, box_y - 2, box_w + 4, box_h + 4))
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h))
        # Read points from Player objects so scoreboard reflects actual points
        p1_score = getattr(self.map_manager.player1, "points", 0)
        p2_score = getattr(self.map_manager.player2, "points", 0)
        score_text = font.render(f"{p1_score}  -  {p2_score}", True, BLACK)
        score_rect = score_text.get_rect(center=(box_x + box_w // 2, box_y + box_h // 2))
        self.screen.blit(score_text, score_rect)

    def render(self):
        self.screen.fill(WHITE)
        self.draw_bases()
        self.draw_objects()
        self.draw_grid()
        self.draw_player_info()
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    if self.map_manager.player1.vehicles or self.map_manager.player2.vehicles:
                        self.current_turn += 1
<<<<<<< HEAD

                        # Guardamos el estado actual del juego antes de avanzar
                        saved_file = self.map_manager.save_game(self.current_turn)
                        print(f"Juego guardado en {saved_file}")
                        # Avanzamos la simulación un paso (MapManager maneja el movimiento)

                        self.map_manager.next_turn()
                        
                        print(f"Avanzando al turno {self.current_turn}")
=======
                        # ACA IRIA LA FUNCION GUARDAR
                        # Advance simulation a single step (MapManager handles vehicle movement)
                        self.map_manager.next_turn(self.current_turn)
                        print(f"Advancing to turn {self.current_turn}")
>>>>>>> 488128571a20360d9b1da6d5dbd1624f0794f298
                    pass
                if event.key == pygame.K_LEFT:
                    if self.current_turn > 0:
                        self.current_turn -= 1
                        print(f"Reverting to turn {self.current_turn}")
                    # Go to previous turn
                    pass
    
    def run(self):
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()