from map_manager import MapManager

m = MapManager(player1_strategy=None, player2_strategy=None, width=10, height=10)
m.new_game()
print('Initial P1 vehicle positions:')
for v in m.player1.vehicles:
    print(v.position, 'capacity', v.capacity)

for t in range(6):
    m.next_turn()
    print('\nAfter turn', t+1)
    for i, v in enumerate(list(m.player1.vehicles)):
        print('P1 v', i, 'pos', v.position, 'load', len(v.load), 'state', getattr(v,'state',None))
    print('Player1 points:', m.player1.points)
