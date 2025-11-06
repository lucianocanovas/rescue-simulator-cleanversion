import pygame
import os
import json
from assets import load_sprite
from map_manager import MapManager
from classes.Mine import Mine

# Constants
# Load visualization constants from config.json when available so CELL_SIZE
# can be adjusted without editing code.
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as _cfg_f:
        _cfg = json.load(_cfg_f)
    _viz = _cfg.get('visualization', {}) if isinstance(_cfg, dict) else {}
    CELL_SIZE = int(_viz.get('cell_size', 16))
    WINDOW_SIZE = int(_viz.get('window_width', CELL_SIZE * 50))
except Exception:
    # Fallbacks
    CELL_SIZE = 16  # default cell size
    WINDOW_SIZE = 800

ROWS = 50
COLUMNS = 50

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 160, 0)

class Visualization:
    def __init__(self, map_manager: MapManager):
        self.map_manager = map_manager
        # Calcular tamaño de ventana dinámicamente con la resolución del mapa
        self.window_size = self.map_manager.width * CELL_SIZE
        # Asegurarse de que la superficie existe (GameEngine debería haber llamado set_mode)
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.current_turn = 0
        self.running = True
        pygame.display.set_caption("Rescue Simulator")
        # Cargar sprite de explosión una vez
        try:
            self.explosion_sprite = load_sprite('explosion.png')
        except Exception:
            self.explosion_sprite = None
        
    def draw_grid(self):
        for x in range(0, self.window_size, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, self.window_size))
        for y in range(0, self.window_size, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (self.window_size, y))
    
    def draw_objects(self):
        # Primero dibujamos todos los sprites de objetos
        for x in range(self.map_manager.width):
            for y in range(self.map_manager.height):
                obj = self.map_manager.grid[x][y]
                if obj is not None:
                    pixel_x = x * CELL_SIZE
                    pixel_y = y * CELL_SIZE
                    scaled_sprite = pygame.transform.scale(obj.sprite, (CELL_SIZE, CELL_SIZE))
                    self.screen.blit(scaled_sprite, (pixel_x, pixel_y))
        
        # Después dibujamos los rectángulos rojos de las minas encima
        for x in range(self.map_manager.width):
            for y in range(self.map_manager.height):
                obj = self.map_manager.grid[x][y]
                if isinstance(obj, Mine):
                    radius_x = obj.x_radius * CELL_SIZE
                    radius_y = obj.y_radius * CELL_SIZE
                    center_x = x * CELL_SIZE + CELL_SIZE // 2
                    center_y = y * CELL_SIZE + CELL_SIZE // 2
                    # Dibujar rectángulo con grosor=2 para mejor visibilidad
                    pygame.draw.rect(self.screen, RED, (center_x - radius_x, center_y - radius_y, radius_x * 2, radius_y * 2), 2)

    def draw_explosions(self):
        # Dibuja círculos en las posiciones registradas como explosiones
        try:
            for ex in getattr(self.map_manager, 'explosions', []):
                pos = ex.get('pos')
                if not pos:
                    continue
                x, y = pos
                # Si disponemos del sprite, dibujarlo centrado ocupando 3x3 celdas
                if self.explosion_sprite is not None:
                    try:
                        size_px = CELL_SIZE * 3
                        sprite_scaled = pygame.transform.scale(self.explosion_sprite, (size_px, size_px))
                        # Top-left para centrar 3x3 sobre la casilla (x,y)
                        top_left_x = x * CELL_SIZE - CELL_SIZE
                        top_left_y = y * CELL_SIZE - CELL_SIZE
                        self.screen.blit(sprite_scaled, (top_left_x, top_left_y))
                        continue
                    except Exception:
                        pass
                # Fallback: dibujar círculo naranja si no hay sprite
                center_x = x * CELL_SIZE + CELL_SIZE // 2
                center_y = y * CELL_SIZE + CELL_SIZE // 2
                radius = max(4, CELL_SIZE // 2)
                pygame.draw.circle(self.screen, ORANGE, (center_x, center_y), radius)
        except Exception:
            pass
    
    def draw_bases(self):
        # Draw Player 1 Base
        pygame.draw.rect(self.screen, BLUE, (0, 0, CELL_SIZE, CELL_SIZE * self.map_manager.height))
        # Draw Player 2 Base
        pygame.draw.rect(self.screen, RED, (self.window_size - CELL_SIZE, 0, CELL_SIZE, CELL_SIZE * self.map_manager.height))

    def draw_player_info(self):
        font = pygame.font.SysFont(None, 40)
        box_w, box_h = 180, 48
        box_x = (self.window_size - box_w) // 2
        box_y = (self.window_size - box_h)
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
        self.draw_explosions()
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

                        # Ejecutamos la simulación para el nuevo turno y luego guardamos
                        # de modo que `turno_N.pkl` refleje el estado DESPUÉS de N turnos.
                        self.map_manager.next_turn(self.current_turn)

                        saved_file = self.map_manager.save_game(self.current_turn)
                        print(f"[INFO] Avanzado al turno: {self.current_turn} — guardado en: {saved_file}")
                    pass
                if event.key == pygame.K_LEFT:
                    if self.current_turn > 0:
                        prev_turn = self.current_turn - 1
                        # Intentamos cargar el turno anterior
                        prev_turn_file = os.path.join(self.map_manager.current_game_folder, f"turno_{prev_turn}.pkl")
                        if os.path.exists(prev_turn_file):
                            # Solo actualizamos current_turn si la carga fue exitosa
                            if self.map_manager.load_game(prev_turn_file, prev_turn):
                                self.current_turn = prev_turn
                                print(f"[INFO] Volviendo al turno: {self.current_turn}")
                            else:
                                print(f"[ERROR] Error al cargar el turno: {prev_turn}")
                        else:
                            print(f"[ERROR] No se encontró el archivo del turno: {prev_turn}")
                    pass
    
    def run(self):
        while self.running:
            # Check for game-over conditions each frame
            try:
                over, reason = self.map_manager.is_game_over()
                if over:
                    # Print a concise message and stop the loop so the game ends
                    reason_map = {
                        'no_vehicles': 'No quedan vehículos. Fin del juego.',
                        'no_items': 'No quedan objetos en la partida. Fin del juego.',
                        'no_reachable_items': 'No hay objetos alcanzables por los vehículos. Fin del juego.'
                    }
                    print(f"[GAME OVER] {reason_map.get(reason, 'Fin del juego.')}")
                    print(f"[INFO] Resultado final: Jugador 1: {self.map_manager.player1.points} puntos | Jugador 2: {self.map_manager.player2.points} puntos")
                    print(f"[INFO] Ganador: {'Jugador 1' if self.map_manager.player1.points > self.map_manager.player2.points else 'Jugador 2' if self.map_manager.player2.points > self.map_manager.player1.points else 'Empate'}")
                    self.running = False
                    # Render one last frame so the player sees the final state
                    self.render()
                    break
            except Exception:
                pass

            self.handle_events()
            self.render()
            self.clock.tick(60)

        pygame.quit()