import os
import pygame

def load_sprite(sprite_path: str):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    path = os.path.join(assets_dir, sprite_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Asset not found: {path}")
    return pygame.image.load(path).convert_alpha()