# Map Class
# @Author: Cesar A. Tacla, UTFPR
#
# A map representing the explored region of the 2D grid
# The map is a dictionaire whose keys are pairs (x, y).
# The map contains only visited positions.
##
# Associated to each key, there are:
# - the degree of difficulty to access the cell
# - the victim seq number (if there is one) or VS.NO_VICTIM if there is no victim
# - the known actions' results from the cell represented as vector of 8 integers, in the following
# order: [up, up-right, right, down-right, down, down-left, left, up-left]. Each position may
# have the following values:
# VS.UNK  the agent ignores if it is possible to go towards the direction (useful if you want
# to not use the check_walls_and_lim method of the AbstAgent and save only tried actions)
# VS.WALL the agent cannot execute the action (there is a wall),
# VS.END  the agent cannot execute the action (end of grid)
# VS.CLEAR the agent can execute the action

from constants import VS


class Position:
    def __init__(self, path_priorities):
        self.coord_x = 0
        self.coord_y = 0
        self.results = {'DOWN-LEFT': None, 'DOWN': None, 'DOWN-RIGHT': None,
                        'LEFT': None, 'UP-RIGHT': None, 'UP': None, 'UP-LEFT': None, 'RIGHT': None}
        self.untried = list(path_priorities)
        self.last_action = ''

    def pop_untried(self):
        if len(self.untried) != 0:
            return self.untried.pop(0)
        else:
            return

    def set_results(self, res, pos):
        self.results[(res)] = pos


class Map:
    def __init__(self, path_priorities):
        self.coord_x = 0
        self.coord_y = 0
        self.coordinates_map = {'DOWN-RIGHT': [1, 1], 'DOWN': [1, 0], 'DOWN-LEFT': [1, -1], 'LEFT': [
            0, -1], 'UP-LEFT': [-1, -1], 'UP': [-1, 0], 'UP-RIGHT': [-1, 1], 'RIGHT': [0, 1]}
        self.path_priorities = path_priorities
        self.position = Position(self.path_priorities)
        self.last_position = Position(self.path_priorities)
        self.last_action = ''
        self.backtracking = False
        self.map_data = {}
        self.map_data = {(0, 0): self.position}

    def in_map(self, coord):
        if coord in self.map_data:
            return True

        return False

    def get(self, coord):
        """ @param coord: a pair (x, y), the key of the dictionary"""
        return self.map_data.get(coord)

    def add(self, coord, difficulty, victim_seq, actions_res):
        """ @param coord: a pair (x, y)
            @param difficulty: the degree of difficulty to acess the cell at coord
            @param victim_seq: the sequential number of the victim returned by the Environment
            @param actions_res: the results of the possible actions from the position (x, y) """
        self.map_data[coord] = (difficulty, victim_seq, actions_res)

    # def draw(self):
    #     if not self.map_data:
    #         print("Map is empty.")
    #         return

    #     min_x = min(key[0] for key in self.map_data.keys())
    #     max_x = max(key[0] for key in self.map_data.keys())
    #     min_y = min(key[1] for key in self.map_data.keys())
    #     max_y = max(key[1] for key in self.map_data.keys())

    #     for y in range(min_y, max_y + 1):
    #         row = ""
    #         for x in range(min_x, max_x + 1):
    #             item = self.get((x, y))
    #             if item:
    #                 if item[1] == VS.NO_VICTIM:
    #                     row += f"[{item[0]:7.2f}  no] "
    #                 else:
    #                     row += f"[{item[0]:7.2f} {item[1]:3d}] "
    #             else:
    #                 row += f"[     ?     ] "
    #         print(row)

    def get_opposite_action(self, action):
        if action == 'RIGHT':
            return 'LEFT'
        elif action == 'UP-RIGHT':
            return 'DOWN-LEFT'
        elif action == 'UP':
            return 'DOWN'
        elif action == 'UP-LEFT':
            return 'DOWN-RIGHT'
        elif action == 'LEFT':
            return 'RIGHT'
        elif action == 'DOWN-LEFT':
            return 'UP-RIGHT'
        elif action == 'DOWN':
            return 'UP'
        elif action == 'DOWN-RIGHT':
            return 'UP-LEFT'
        else:
            return

    def get_action(self):
        self.backtracking = False
        mov = (0, 0)
        action = ''
        while (self.coord_x+mov[1], self.coord_y+mov[0]) in self.map_data and action is not None:
            action = self.position.pop_untried()
            if action is not None:
                mov = self.coordinates_map[action]
                self.last_action = action

        if action is None:
            action = self.get_opposite_action(self.last_action)
            mov = self.coordinates_map[action]
            self.backtracking = True
            self.last_action = action
        return mov

    def update_agent_position(self, dx, dy):
        self.coord_x = self.coord_x + dx
        self.coord_y = self.coord_y + dy

        if (self.coord_x, self.coord_y) not in self.map:
            pos = Position(self.path_priorities)
            pos.coord_x = self.coord_x
            pos.coord_y = self.coord_y
            self.map[(self.coord_x, self.coord_y)] = pos
            pos.last_action = self.last_action
        else:
            pos = self.map[(self.coord_x, self.coord_y)]
            if self.backtracking is not True:
                pos.last_action = self.last_action
        self.position.set_results(self.last_action, pos)
        pos.set_results(self.get_opposite_action(
            self.last_action), self.position)
        self.last_position = self.position
        self.position = pos

    def is_position_known(self, x, y):
        """ Verifica se a posição (x, y) já foi visitada """
        return (x, y) in self.map_data
