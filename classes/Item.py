from assets import load_sprite

class Item:
    def __init__(self, value: int, position: tuple[int, int], sprite: str):
        self.value = value
        self.position = position
        try:
            self.sprite = load_sprite(sprite)
        except Exception as e:
            # Mensaje de error uniforme en español
            print(f"[ERROR] Error al cargar sprite de item: {e}")
            self.sprite = None

class Person(Item):
    def __init__(self, position: tuple[int, int]):
        super().__init__(value=50, position=position, sprite="person.png")

class Weapon(Item):
    def __init__(self, position: tuple[int, int]):
        super().__init__(value=50, position=position, sprite="weapon.png")

class Clothing(Item):
    def __init__(self, position: tuple[int, int]):
        super().__init__(value=5, position=position, sprite="clothes.png")

class Food(Item):
    def __init__(self, position: tuple[int, int]):
        super().__init__(value=10, position=position, sprite="food.png")

class Heal(Item):
    def __init__(self, position: tuple[int, int]):
        super().__init__(value=20, position=position, sprite="heal.png")