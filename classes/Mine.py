from assets import load_sprite

class Mine:
    def __init__(self, position: tuple[int, int], x_radius: int, y_radius: int, sprite: str):
        self.position = position
        self.x_radius = x_radius
        self.y_radius = y_radius
        try:
            self.sprite = load_sprite(sprite)
        except Exception as e:
            print(f"Error loading sprite: {e}")
            self.sprite = None

class Mine_O1(Mine):
    def __init__(self, position: tuple[int, int]):
        super().__init__(position, x_radius=10, y_radius=10, sprite="mine_O1.png")

class Mine_O2(Mine):
    def __init__(self, position: tuple[int, int]):
        super().__init__(position, x_radius=5, y_radius=5, sprite="mine_O2.png")

class Mine_T1(Mine):
    def __init__(self, position: tuple[int, int]):
        super().__init__(position, x_radius=10, y_radius=1, sprite="mine_T1.png")

class Mine_T2(Mine):
    def __init__(self, position: tuple[int, int]):
        super().__init__(position, x_radius=1, y_radius=5, sprite="mine_T2.png")

class Mine_G1(Mine):
    def __init__(self, position: tuple[int, int]):
        super().__init__(position, x_radius=7, y_radius=7, sprite="mine_G1.png")

    def toggle(self):
        if self.x_radius == 7 and self.y_radius == 7:
            self.x_radius = 0
            self.y_radius = 0
        else:
            self.x_radius = 7
            self.y_radius = 7