from map_manager import MapManager

map_manager = MapManager(player1_strategy=None, player2_strategy=None, width=10, height=10)
map_manager.new_game()
print("[INFO] Posiciones iniciales de vehículos del Jugador 1:")
for vehicle in map_manager.player1.vehicles:
    print(f"  - Posición: {vehicle.position} | Capacidad: {vehicle.capacity}")

for turno in range(6):
    map_manager.next_turn(turno)
    print(f"\n[INFO] Estado después del turno {turno + 1}:")
    for idx, vehicle in enumerate(list(map_manager.player1.vehicles)):
        print(f"  - Vehículo P1 #{idx}: pos={vehicle.position} load={len(vehicle.load)} state={getattr(vehicle,'state',None)}")
    print(f"[INFO] Puntos Jugador 1: {map_manager.player1.points}")
