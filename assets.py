import os
import pygame

def load_sprite(sprite_path: str):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    path = os.path.join(assets_dir, sprite_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Asset not found: {path}")
    return pygame.image.load(path).convert_alpha()

def load_sound(sound_path: str):
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        path = os.path.join(assets_dir, sound_path)
        if not os.path.isfile(path):
            print(f"[WARNING] Archivo de sonido no encontrado: {path}")
            return None
        return pygame.mixer.Sound(path)
    except Exception as e:
        print(f"[ERROR] Error al cargar sonido {sound_path}: {e}")
        return None

def load_font(font_path: str, size: int):
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        path = os.path.join(assets_dir, font_path)
        if not os.path.isfile(path):
            print(f"[WARNING] Archivo de fuente no encontrado: {path}, usando fuente por defecto")
            return pygame.font.SysFont(None, size)
        return pygame.font.Font(path, size)
    except Exception as e:
        print(f"[ERROR] Error al cargar fuente {font_path}: {e}, usando fuente por defecto")
        return pygame.font.SysFont(None, size)
