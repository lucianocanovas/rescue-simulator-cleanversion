import os
import pygame

def load_sprite(sprite_path: str):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    path = os.path.join(assets_dir, sprite_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Asset not found: {path}")
    return pygame.image.load(path).convert_alpha()

def load_sound(sound_path: str):
    """Carga un archivo de sonido desde la carpeta assets.
    
    Args:
        sound_path: Nombre del archivo de sonido (ej: 'unload.mp3')
    
    Returns:
        pygame.mixer.Sound object o None si no se puede cargar
    """
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