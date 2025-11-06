import os
import pygame

def load_sprite(sprite_path: str):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    path = os.path.join(assets_dir, sprite_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Asset not found: {path}")
    # Cargamos la imagen. convert_alpha() requiere que exista un display activo
    # en algunas plataformas, así que solo lo llamamos si la superficie ya existe.
    surf = pygame.image.load(path)
    try:
        if pygame.display.get_surface() is not None:
            return surf.convert_alpha()
    except Exception:
        # Si por alguna razón pygame falla al comprobar el surface, devolvemos la
        # Surface sin convertir; funcionará aunque no esté optimizada.
        pass
    return surf