import pygame
import os
import json
from assets import load_sprite, load_sound, load_font
from map_manager import MapManager
from classes.Mine import Mine
from classes.Vehicle import Vehicle, Truck, Jeep, Car, Motorcycle

# Load visualization constants from config.json when available
# so CELL_SIZE can be adjusted without editing code
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    visualization_config = config.get('visualization', {}) if isinstance(config, dict) else {}
    CELL_SIZE = int(visualization_config.get('cell_size', 16))
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
        # Calculate window size dynamically with map resolution
        self.window_size = self.map_manager.width * CELL_SIZE
        # Ensure surface exists (GameEngine should have called set_mode)
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.current_turn = 0
        self.autoplay = False
        # Read autoplay delay (ms) from config.json, fall back to 1000 ms
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
            visualization_config = config.get('visualization', {}) if isinstance(config, dict) else {}
            self.autoplay_delay = int(visualization_config.get('autoplay_delay', 1000))
        except Exception:
            self.autoplay_delay = 1000
        self.last_autoplay_time = pygame.time.get_ticks()
        self.running = True
        pygame.display.set_caption("Rescue Simulator")
        # Load explosion sprite once
        try:
            self.explosion_sprite = load_sprite('explosion.png')
        except Exception:
            self.explosion_sprite = None
        # Load victory sound
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
        # First draw all object sprites
        for x in range(self.map_manager.width):
            for y in range(self.map_manager.height):
                grid_object = self.map_manager.grid[x][y]
                if grid_object is not None:
                    pixel_x = x * CELL_SIZE
                    pixel_y = y * CELL_SIZE
                    
                    # If it's a vehicle, draw colored background with transparency
                    if isinstance(grid_object, Vehicle):
                        background_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        
                        # Determine color based on vehicle type
                        if isinstance(grid_object, Truck):
                            color = (255, 0, 0)  # Red
                        elif isinstance(grid_object, Jeep):
                            color = (255, 255, 0)  # Yellow
                        elif isinstance(grid_object, Car):
                            color = (255, 165, 0)  # Orange
                        elif isinstance(grid_object, Motorcycle):
                            color = (0, 255, 0)  # Green
                        else:
                            color = (200, 200, 200)  # Default gray
                        
                        background_surface.fill(color)
                        self.screen.blit(background_surface, (pixel_x, pixel_y))
                    
                    scaled_sprite = pygame.transform.scale(grid_object.sprite, (CELL_SIZE, CELL_SIZE))
                    self.screen.blit(scaled_sprite, (pixel_x, pixel_y))
        
        # Then draw the red rectangles of mines on top
        for x in range(self.map_manager.width):
            for y in range(self.map_manager.height):
                grid_object = self.map_manager.grid[x][y]
                if isinstance(grid_object, Mine):
                    radius_x = grid_object.x_radius * CELL_SIZE
                    radius_y = grid_object.y_radius * CELL_SIZE
                    center_x = x * CELL_SIZE + CELL_SIZE // 2
                    center_y = y * CELL_SIZE + CELL_SIZE // 2
                    # Draw rectangle with thickness=2 for better visibility
                    pygame.draw.rect(self.screen, RED, (center_x - radius_x, center_y - radius_y, radius_x * 2, radius_y * 2), 2)

    def draw_explosions(self):
        try:
            for explosion in getattr(self.map_manager, 'explosions', []):
                position = explosion.get('pos')
                if not position:
                    continue
                explosion_x, explosion_y = position
                # If explosion sprite available, draw it centered occupying 3x3 cells
                if self.explosion_sprite is not None:
                    try:
                        size_pixels = CELL_SIZE * 3
                        sprite_scaled = pygame.transform.scale(self.explosion_sprite, (size_pixels, size_pixels))
                        # Top-left to center 3x3 over cell (x,y)
                        top_left_x = explosion_x * CELL_SIZE - CELL_SIZE
                        top_left_y = explosion_y * CELL_SIZE - CELL_SIZE
                        self.screen.blit(sprite_scaled, (top_left_x, top_left_y))
                        continue
                    except Exception:
                        pass
                # Fallback: draw orange circle if no sprite
                center_x = explosion_x * CELL_SIZE + CELL_SIZE // 2
                center_y = explosion_y * CELL_SIZE + CELL_SIZE // 2
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
        font = load_font('minecraft.ttf', 32)
        box_width, box_height = 180, 50
        box_x = (self.window_size - box_width) // 2
        box_y = (self.window_size - box_height)
        
        # Create transparent surfaces for background
        # Black border with 50% opacity
        border_surface = pygame.Surface((box_width + 4, box_height + 4), pygame.SRCALPHA)
        border_surface.fill((0, 0, 0, 64))  # RGBA: black with alpha=64
        self.screen.blit(border_surface, (box_x - 2, box_y - 2))
        
        # White background with transparency
        background_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        background_surface.fill((255, 255, 255, 0))  # RGBA: white with alpha=0
        self.screen.blit(background_surface, (box_x, box_y))
        
        # Read points from Player objects so scoreboard reflects actual points
        player1_score = getattr(self.map_manager.player1, "points", 0)
        player2_score = getattr(self.map_manager.player2, "points", 0)
        score_text = font.render(f"{player1_score}  -  {player2_score}", True, BLACK)
        score_rect = score_text.get_rect(center=(box_x + box_width // 2, box_y + box_height // 2))
        self.screen.blit(score_text, score_rect)

        # Show current turn number in the upper part
        turn_font = load_font('minecraft.ttf', 32)
        turn_text = turn_font.render(f"{self.current_turn}", True, BLACK)
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
    
    def show_controls_screen(self):
        # Load key images
        try:
            arrow_left = load_sprite('ARROWLEFT.png')
            arrow_right = load_sprite('ARROWRIGHT.png')
            space_key = load_sprite('SPACE.png')
        except Exception as error:
            print(f"❌ - ERROR LOADING CONTROL SPRITES: {error}")
            arrow_left = None
            arrow_right = None
            space_key = None
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    waiting = False
            
            # Draw game state in background
            self.screen.fill(WHITE)
            self.draw_bases()
            self.draw_objects()
            self.draw_grid()
            
            # Dark semi-transparent overlay over the board
            overlay = pygame.Surface((self.window_size, self.window_size), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))  # Black with 78% opacity
            self.screen.blit(overlay, (0, 0))
            
            # Main title
            title_font = load_font('minecraft.ttf', 72)
            title_text = title_font.render("RESCUE SIMULATOR", True, WHITE)
            title_rect = title_text.get_rect(center=(self.window_size // 2, 100))
            self.screen.blit(title_text, title_rect)
            
            # Layout configuration
            key_size = 70
            description_font = load_font('minecraft.ttf', 32)
            
            # Initial position below title
            start_y = 200
            
            # Spacing between each complete block (image + text + margin)
            block_spacing = 160
            text_offset = 10
            
            # Control 1: Arrow Left
            current_y = start_y
            if arrow_left:
                # Centered image
                arrow_left_scaled = pygame.transform.scale(arrow_left, (key_size, key_size))
                image_rect = arrow_left_scaled.get_rect(center=(self.window_size // 2, current_y))
                self.screen.blit(arrow_left_scaled, image_rect)
                
                # Text centered below image
                text_y = current_y + key_size + text_offset
                description_text = description_font.render("PREVIOUS TURN", True, WHITE)
                description_rect = description_text.get_rect(center=(self.window_size // 2, text_y))
                self.screen.blit(description_text, description_rect)
            
            # Control 2: Arrow Right
            current_y = start_y + block_spacing
            if arrow_right:
                # Centered image
                arrow_right_scaled = pygame.transform.scale(arrow_right, (key_size, key_size))
                image_rect = arrow_right_scaled.get_rect(center=(self.window_size // 2, current_y))
                self.screen.blit(arrow_right_scaled, image_rect)
                
                # Text centered below image
                text_y = current_y + key_size + text_offset
                description_text = description_font.render("NEXT TURN", True, WHITE)
                description_rect = description_text.get_rect(center=(self.window_size // 2, text_y))
                self.screen.blit(description_text, description_rect)
            
            # Control 3: Space
            current_y = start_y + block_spacing * 2
            if space_key:
                # Centered image (wider)
                space_scaled = pygame.transform.scale(space_key, (key_size * 2.5, key_size))
                image_rect = space_scaled.get_rect(center=(self.window_size // 2, current_y))
                self.screen.blit(space_scaled, image_rect)
                
                # Text centered below image
                text_y = current_y + key_size + text_offset
                description_text = description_font.render("TOGGLE AUTOPLAY", True, WHITE)
                description_rect = description_text.get_rect(center=(self.window_size // 2, text_y))
                self.screen.blit(description_text, description_rect)
            
            # Instruction to start
            continue_font = load_font('minecraft.ttf', 24)
            continue_text = continue_font.render("PRESS ANY KEY TO START", True, (255, 255, 255))
            continue_rect = continue_text.get_rect(center=(self.window_size // 2, self.window_size - 50))
            self.screen.blit(continue_text, continue_rect)
            
            pygame.display.flip()
            self.clock.tick(30)
    
    def show_game_over_screen(self, reason):
        
        # Play victory sound with reduced volume
        if self.victory_sound is not None:
            try:
                self.victory_sound.set_volume(0.3)  # 30% volume (0.0 to 1.0)
                self.victory_sound.play()
            except Exception:
                pass

        # Determine the winner
        player1_score = self.map_manager.player1.points
        player2_score = self.map_manager.player2.points
        
        if player1_score > player2_score:
            winner_text = "¡PLAYER 1 WINS!"
            winner_color = BLUE
        elif player2_score > player1_score:
            winner_text = "¡PLAYER 2 WINS!"
            winner_color = RED
        else:
            winner_text = "¡TIE!"
            winner_color = BLACK
        
        # End reason message
        reason_map = {
            'no_vehicles': 'NO VEHICLES LEFT',
            'no_items': 'NO ITEMS LEFT',
            'no_reachable_items': 'NO REACHABLE ITEMS LEFT'
        }
        reason_text = reason_map.get(reason, 'Game Over')
        
        # Game over screen loop
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    waiting = False
            
            # Draw final game state
            self.screen.fill(WHITE)
            self.draw_bases()
            self.draw_objects()
            self.draw_explosions()
            self.draw_grid()
            
            # Semi-transparent overlay
            overlay = pygame.Surface((self.window_size, self.window_size), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
            self.screen.blit(overlay, (0, 0))
            
            # "GAME OVER" title
            title_font = load_font('minecraft.ttf', 72)
            title_text = title_font.render("GAME OVER", True, WHITE)
            title_rect = title_text.get_rect(center=(self.window_size // 2, self.window_size // 3))
            self.screen.blit(title_text, title_rect)
            
            # End reason
            reason_font = load_font('minecraft.ttf', 32)
            reason_render = reason_font.render(reason_text, True, GRAY)
            reason_rect = reason_render.get_rect(center=(self.window_size // 2, self.window_size // 3 + 60))
            self.screen.blit(reason_render, reason_rect)
            
            # Winner
            winner_font = load_font('minecraft.ttf', 48)
            winner_render = winner_font.render(winner_text, True, winner_color)
            winner_rect = winner_render.get_rect(center=(self.window_size // 2, self.window_size // 2))
            self.screen.blit(winner_render, winner_rect)
            
            # Scores
            score_font = load_font('minecraft.ttf', 48)
            score_text = score_font.render(f"PLAYER 1: {player1_score}", True, BLUE)
            score_rect = score_text.get_rect(center=(self.window_size // 2, self.window_size // 2 + 80))
            self.screen.blit(score_text, score_rect)
            
            score_text2 = score_font.render(f"PLAYER 2: {player2_score}", True, RED)
            score_rect2 = score_text2.get_rect(center=(self.window_size // 2, self.window_size // 2 + 130))
            self.screen.blit(score_text2, score_rect2)
            
            # Instruction to continue
            continue_font = load_font('minecraft.ttf', 28)
            continue_text = continue_font.render("PRESS ANY KEY TO CONTINUE", True, WHITE)
            continue_rect = continue_text.get_rect(center=(self.window_size // 2, self.window_size - 50))
            self.screen.blit(continue_text, continue_rect)
            
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
                        print("▶️ - AUTOPLAY: ON")
                        self.last_autoplay_time = pygame.time.get_ticks()
                    else:
                        print("⏸️ - AUTOPLAY: OFF")
                if event.key == pygame.K_RIGHT:
                    if self.map_manager.player1.vehicles or self.map_manager.player2.vehicles:
                        self.current_turn += 1

                        # Execute simulation for new turn and then save
                        self.map_manager.next_turn(self.current_turn)

                        saved_file = self.map_manager.save_game(self.current_turn)
                        print(f"⏩ - ADVANCING TO TURN: {self.current_turn} — SAVED: {saved_file}")
                    pass
                if event.key == pygame.K_LEFT:
                    if self.current_turn > 0:
                        previous_turn = self.current_turn - 1
                        # Try to load previous turn
                        previous_turn_file = os.path.join(self.map_manager.current_game_folder, f"turn_{previous_turn}.pkl")
                        if os.path.exists(previous_turn_file):
                            # Only update current_turn if load was successful
                            if self.map_manager.load_game(previous_turn_file, previous_turn):
                                self.current_turn = previous_turn
                                print(f"⏪ - RETURNED TO TURN: {self.current_turn}")
                            else:
                                print(f"❌ - ERROR LOADING TURN: {previous_turn}")
                        else:
                            print(f"❌ - TURN FILE NOT FOUND: {previous_turn_file}")
                    pass
    
    def run(self):
        # Show controls screen before starting
        self.show_controls_screen()
        
        # If user closed window on controls screen, exit
        if not self.running:
            return
        
        while self.running:
            # Check for game-over conditions each frame
            try:
                is_over, reason = self.map_manager.is_game_over()
                if is_over:
                    # Print a concise message
                    reason_map = {
                        'no_vehicles': 'NO VEHICLES LEFT.',
                        'no_items': 'NO ITEMS LEFT.',
                        'no_reachable_items': 'NO REACHABLE ITEMS LEFT.'
                    }
                    print(f"ℹ️ - GAME OVER: {reason_map.get(reason, '')}")
                    print(f"ℹ️ - FINAL RESULTS: Player 1: {self.map_manager.player1.points}, Player 2: {self.map_manager.player2.points}")
                    print(f"ℹ️ - WINNER: {'PLAYER 1' if self.map_manager.player1.points > self.map_manager.player2.points else 'PLAYER 2' if self.map_manager.player2.points > self.map_manager.player1.points else 'TIE'}")
                    
                    # Generate CSV file with statistics before showing end screen
                    try:
                        csv_file = self.map_manager.generate_game_stats_csv(reason)
                        if csv_file:
                            print(f"📊 - GAME STATISTICS SAVED: {csv_file}")
                    except Exception as error:
                        print(f"❌ - ERROR GENERATING STATISTICS: {error}")
                    
                    # Show game over screen
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
                        print(f"⏩ - AUTOPLAY ADVANCING TO TURN: {self.current_turn} — SAVED: {saved_file}")
                        self.last_autoplay_time = current_time
                    else:
                        # No vehicles left, stop autoplay
                        self.autoplay = False
                        print("⏸️ - AUTOPLAY: OFF (NO VEHICLES LEFT)")
            
            self.render()
            self.clock.tick(60)

        pygame.quit()