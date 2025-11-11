import pygame
import os
import json
from assets import load_sprite, load_sound
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
    WINDOW_SIZE = CELL_SIZE * 50
except Exception:
    CELL_SIZE = 16
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
        self.autoplay = False
        # Read autoplay delay (ms) from config.json, fall back to 1000 ms
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as _cfg_f:
                _cfg = json.load(_cfg_f)
            _viz = _cfg.get('visualization', {}) if isinstance(_cfg, dict) else {}
            self.autoplay_delay = int(_viz.get('autoplay_delay', 1000))
        except Exception:
            self.autoplay_delay = 1000
        self.last_autoplay_time = pygame.time.get_ticks()
        self.running = True
        pygame.display.set_caption("Rescue Simulator")
        # Cargar sprite de explosión una vez
        try:
            self.explosion_sprite = load_sprite('explosion.png')
        except Exception:
            self.explosion_sprite = None
        # Cargar sonido de victoria
        try:
            self.victory_sound = load_sound('victory.mp3')
        except Exception:
            self.victory_sound = None
        
    def draw_grid(self):
        for x in range(0, self.window_size, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, self.window_size))
        for y in range(0, self.window_size, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (self.window_size, y))
    
    def draw_objects(self):
        from classes.Vehicle import Vehicle, Truck, Jeep, Car, Motorcycle
        
        # Primero dibujamos todos los sprites de objetos
        for x in range(self.map_manager.width):
            for y in range(self.map_manager.height):
                obj = self.map_manager.grid[x][y]
                if obj is not None:
                    pixel_x = x * CELL_SIZE
                    pixel_y = y * CELL_SIZE
                    
                    # Si es un vehículo, dibujar fondo de color con transparencia
                    if isinstance(obj, Vehicle):
                        bg_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        
                        # Determinar color según tipo de vehículo
                        if isinstance(obj, Truck):
                            color = (255, 0, 0)  # Rojo con 50% transparencia
                        elif isinstance(obj, Jeep):
                            color = (255, 255, 0)  # Amarillo con 50% transparencia
                        elif isinstance(obj, Car):
                            color = (255, 165, 0)  # Naranja con 50% transparencia
                        elif isinstance(obj, Motorcycle):
                            color = (0, 255, 0)  # Verde con 50% transparencia
                        else:
                            color = (200, 200, 200)  # Gris por defecto
                        
                        bg_surface.fill(color)
                        self.screen.blit(bg_surface, (pixel_x, pixel_y))
                    
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
        
        # Crear superficies con transparencia para el fondo
        # Borde negro con 50% de opacidad
        border_surface = pygame.Surface((box_w + 4, box_h + 4), pygame.SRCALPHA)
        border_surface.fill((0, 0, 0, 64))  # RGBA: negro con alpha=128 (50%)
        self.screen.blit(border_surface, (box_x - 2, box_y - 2))
        
        # Fondo blanco con 50% de opacidad
        bg_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surface.fill((255, 255, 255, 64))  # RGBA: blanco con alpha=128 (50%)
        self.screen.blit(bg_surface, (box_x, box_y))
        
        # Read points from Player objects so scoreboard reflects actual points
        p1_score = getattr(self.map_manager.player1, "points", 0)
        p2_score = getattr(self.map_manager.player2, "points", 0)
        score_text = font.render(f"{p1_score}  -  {p2_score}", True, BLACK)
        score_rect = score_text.get_rect(center=(box_x + box_w // 2, box_y + box_h // 2))
        self.screen.blit(score_text, score_rect)

        # Show current turn number in the upper part
        turn_font = pygame.font.SysFont(None, 28)
        turn_text = turn_font.render(f"Turn: {self.current_turn}", True, BLACK)
        turn_rect = turn_text.get_rect(center=(self.window_size // 2, 20))
        self.screen.blit(turn_text, turn_rect)

    def render(self):
        self.screen.fill(WHITE)
        self.draw_bases()
        self.draw_objects()
        self.draw_explosions()
        self.draw_grid()
        self.draw_player_info()
        pygame.display.flip()
    
    def show_game_over_screen(self, reason):
        """Muestra la pantalla de fin de juego y espera a que el usuario presione una tecla."""
        
        # Reproducir sonido de victoria con volumen reducido
        if self.victory_sound is not None:
            try:
                self.victory_sound.set_volume(0.3)  # 30% del volumen (0.0 a 1.0)
                self.victory_sound.play()
            except Exception:
                pass

        # Determinar el ganador
        p1_score = self.map_manager.player1.points
        p2_score = self.map_manager.player2.points
        
        if p1_score > p2_score:
            winner_text = "¡JUGADOR 1 GANA!"
            winner_color = BLUE
        elif p2_score > p1_score:
            winner_text = "¡JUGADOR 2 GANA!"
            winner_color = RED
        else:
            winner_text = "¡EMPATE!"
            winner_color = BLACK
        
        # Mensaje de razón del fin
        reason_map = {
            'no_vehicles': 'No quedan vehículos',
            'no_items': 'No quedan objetos',
            'no_reachable_items': 'No hay objetos alcanzables'
        }
        reason_text = reason_map.get(reason, 'Fin del juego')
        
        # Loop de la pantalla de game over
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    waiting = False
            
            # Dibujar el estado final del juego
            self.screen.fill(WHITE)
            self.draw_bases()
            self.draw_objects()
            self.draw_explosions()
            self.draw_grid()
            
            # Overlay semi-transparente
            overlay = pygame.Surface((self.window_size, self.window_size), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Negro con 70% opacidad
            self.screen.blit(overlay, (0, 0))
            
            # Título "FIN DEL JUEGO"
            title_font = pygame.font.SysFont(None, 72)
            title_text = title_font.render("FIN DEL JUEGO", True, WHITE)
            title_rect = title_text.get_rect(center=(self.window_size // 2, self.window_size // 3))
            self.screen.blit(title_text, title_rect)
            
            # Razón del fin
            reason_font = pygame.font.SysFont(None, 32)
            reason_render = reason_font.render(reason_text, True, GRAY)
            reason_rect = reason_render.get_rect(center=(self.window_size // 2, self.window_size // 3 + 60))
            self.screen.blit(reason_render, reason_rect)
            
            # Ganador
            winner_font = pygame.font.SysFont(None, 64)
            winner_render = winner_font.render(winner_text, True, winner_color)
            winner_rect = winner_render.get_rect(center=(self.window_size // 2, self.window_size // 2))
            self.screen.blit(winner_render, winner_rect)
            
            # Puntuaciones
            score_font = pygame.font.SysFont(None, 48)
            score_text = score_font.render(f"Jugador 1: {p1_score} pts", True, BLUE)
            score_rect = score_text.get_rect(center=(self.window_size // 2, self.window_size // 2 + 80))
            self.screen.blit(score_text, score_rect)
            
            score_text2 = score_font.render(f"Jugador 2: {p2_score} pts", True, RED)
            score_rect2 = score_text2.get_rect(center=(self.window_size // 2, self.window_size // 2 + 130))
            self.screen.blit(score_text2, score_rect2)
            
            # Instrucción para continuar
            continue_font = pygame.font.SysFont(None, 28)
            continue_text = continue_font.render("Presiona cualquier tecla para salir", True, WHITE)
            continue_rect = continue_text.get_rect(center=(self.window_size // 2, self.window_size - 50))
            self.screen.blit(continue_text, continue_rect)
            

        # Reproducible: play victory sound once (non-blocking)
            
            pygame.display.flip()
            self.clock.tick(30)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Toggle autoplay on/off
                    self.autoplay = not self.autoplay
                    if self.autoplay:
                        print("[INFO] Autoplay activado")
                        self.last_autoplay_time = pygame.time.get_ticks()
                    else:
                        print("[INFO] Autoplay desactivado")
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
                    # Print a concise message
                    reason_map = {
                        'no_vehicles': 'No quedan vehículos. Fin del juego.',
                        'no_items': 'No quedan objetos en la partida. Fin del juego.',
                        'no_reachable_items': 'No hay objetos alcanzables por los vehículos. Fin del juego.'
                    }
                    print(f"[GAME OVER] {reason_map.get(reason, 'Fin del juego.')}")
                    print(f"[INFO] Resultado final: Jugador 1: {self.map_manager.player1.points} puntos | Jugador 2: {self.map_manager.player2.points} puntos")
                    print(f"[INFO] Ganador: {'Jugador 1' if self.map_manager.player1.points > self.map_manager.player2.points else 'Jugador 2' if self.map_manager.player2.points > self.map_manager.player1.points else 'Empate'}")
                    
                    # Mostrar pantalla de fin de juego
                    self.show_game_over_screen(reason)
                    self.running = False
                    break
            except Exception:
                pass

            self.handle_events()
            
            # Autoplay logic: advance turn every second if autoplay is True
            if self.autoplay:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_autoplay_time >= self.autoplay_delay:
                    # Check if there are vehicles before advancing
                    if self.map_manager.player1.vehicles or self.map_manager.player2.vehicles:
                        self.current_turn += 1
                        self.map_manager.next_turn(self.current_turn)
                        saved_file = self.map_manager.save_game(self.current_turn)
                        print(f"[AUTOPLAY] Turno: {self.current_turn} — guardado en: {saved_file}")
                        self.last_autoplay_time = current_time
                    else:
                        # No vehicles left, stop autoplay
                        self.autoplay = False
                        print("[INFO] Autoplay desactivado - No quedan vehículos")
            
            self.render()
            self.clock.tick(60)

        pygame.quit()