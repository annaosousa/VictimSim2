# EXPLORER AGENT
# @Author: Tacla, UTFPR
#
# It walks randomly in the environment looking for victims. When half of the
# exploration has gone, the explorer goes back to the base.

import heapq
from queue import PriorityQueue
import sys
import os
import random
import math
from abc import ABC, abstractmethod
from abstract_agent import AbstAgent
from rescuer import Rescuer
from constants import VS
from map import Map


class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()

    def is_empty(self):
        return len(self.items) == 0


class Explorer(AbstAgent):
    def __init__(self, env, config_file, resc, path_priorities):
        """ Construtor do agente random on-line
        @param env: a reference to the environment 
        @param config_file: the absolute path to the explorer's config file
        @param resc: a reference to the rescuer agent to invoke when exploration finishes
        """

        super().__init__(env, config_file)
        self.walk_stack = Stack()  # a stack to store the movements
        self.set_state(VS.ACTIVE)  # explorer is active since the begin
        self.resc = resc           # reference to the rescuer agent
        self.x = 0                 # current x position relative to the origin 0
        self.y = 0                 # current y position relative to the origin 0
        # set the time to come back to the base
        self.time_to_comeback = math.ceil(self.TLIM * 0.6)
        # create a map for representing the environment
        self.map = Map(path_priorities)
        # a dictionary of found victims: (seq): ((x,y), [<vs>])
        self.victims = {}
        # the key is the seq number of the victim,(x,y) the position, <vs> the list of vital signals

        # put the current position - the base - in the map
        self.map.add((self.x, self.y), 1, VS.NO_VICTIM,
                     self.check_walls_and_lim())

        # self.set_known_map = []
        self.map_graph = {}
        self.known_map = []
        self.known_victims = []
        self.resc = resc
        self.last_position = ''
        self.visited_position = set()
        # Define a pilha de posições visitadas
        self.position_stack = []

    def explore_with_backtracking(self, x, y, position_stack):
        """ Recursively explores the map with backtracking from position (x, y). """
        # Marca a posição como visitada
        self.map.mark_position_as_known(x, y)
        self.visited_position.add((x, y))

        # Define as direções possíveis (cima, baixo, esquerda, direita)
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        # Embaralha as direções para explorar aleatoriamente
        random.shuffle(directions)

        # Explora recursivamente em cada direção
        for dx, dy in directions:
            next_x, next_y = x + dx, y + dy
            if self.explore_with_backtracking(next_x, next_y, position_stack):
                return True  # Indica que houve exploração nesta direção

        # Se não houver direções possíveis, volta para a última posição visitada com direções não exploradas
        while position_stack:
            last_x, last_y = position_stack.pop()
            if (last_x, last_y) in self.visited_position:
                continue  # Já visitou essa posição, passa para a próxima
            return self.explore_with_backtracking(last_x, last_y, position_stack)

        return False  # Indica que não houve exploração nesta direção e não há posições para voltar

    def get_next_position(self, direction):
        """ Gets the next position that can be explored (no wall and inside the grid). """
        # Verifica as direções possíveis para se mover a partir da posição atual
        obstacles = self.check_walls_and_lim()

        # Lista de direções possíveis
        directions = list(range(8))
        # Embaralha as direções para explorar aleatoriamente
        # random.shuffle(directions)

        direction = self.map.path_priorities

        # Loop até encontrar uma posição não visitada ou todas as direções serem exploradas
        for dir in direction:
            dx, dy = Explorer.AC_INCR[dir]

            # Verifica se a próxima posição é clara e não visitada
            if self.authorize(obstacles, dx, dy) == VS.CLEAR:
                next_x, next_y = self.x + dx, self.y + dy
                if not self.map.is_position_known(next_x, next_y):
                    # Armazena a posição atual na pilha de posições visitadas
                    self.position_stack.append((self.x, self.y))
                    return dx, dy
                # else:
                    # Se todas as direções levarem a posições conhecidas, inicia o backtracking
                    # self.explore_with_backtracking(
                    #     next_x, next_y, self.position_stack)
        if not self.position_stack:
            return 0, 0

        prev_x, prev_y = self.position_stack.pop()
        dx = prev_x - self.x
        dy = prev_y - self.y
        # Se todas as direções levarem a posições conhecidas, retorna 0, 0 (ficar parado)
        return dx, dy

    def explore(self):
        # Check the neighborhood obstacles
        obstacles = self.check_walls_and_lim()

        # get an random increment for x and y
        # mov = self.map.get_action()
        # dy = mov[0]
        # dx = mov[1]

        dx, dy = self.get_next_position(self.map.path_priorities)

        # while not self.authorize(obstacles, dx, dy):
        #     mov = self.map.get_action()
        #     dy = mov[0]
        #     dx = mov[1]

        self.update_known_map()

        # Moves the body to another position
        rtime_bef = self.get_rtime()
        result = self.walk(dx, dy)
        rtime_aft = self.get_rtime()

        # self.set_known_map()

        # Test the result of the walk action
        # Should never bump, but for safe functionning let's test
        if result == VS.BUMPED:
            # update the map with the wall
            self.map.add((self.x + dx, self.y + dy), VS.OBST_WALL,
                         VS.NO_VICTIM, self.check_walls_and_lim())
            # print(f"""{self.NAME}: Wall or grid limit reached at ({
            #       self.x + dx}, {self.y + dy})""")

        if result == VS.EXECUTED:
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            self.walk_stack.push((dx, dy))

            # update the agent's position relative to the origin
            self.x += dx
            self.y += dy

            # Check for victims
            seq = self.check_for_victim()
            if seq != VS.NO_VICTIM:
                vs = self.read_vital_signals()
                self.victims[vs[0]] = ((self.x, self.y), vs)
                print(f"""{self.NAME} Victim found at ({self.x}, {
                      self.y}), rtime: {self.get_rtime()}""")
                self.known_victims.append([self.x, self.y])
                # print(f"{self.NAME} Seq: {seq} Vital signals: {vs}")

            # Calculates the difficulty of the visited cell
            difficulty = (rtime_bef - rtime_aft)
            if dx == 0 or dy == 0:
                difficulty = difficulty / self.COST_LINE
            else:
                difficulty = difficulty / self.COST_DIAG

            # Update the map with the new cell
            self.map.add((self.x, self.y), difficulty,
                         seq, self.check_walls_and_lim())
            print(f"""{self.NAME}:at ({self.x}, {self.y}), diffic: {
                  difficulty:.2f} vict: {seq} rtime: {self.get_rtime()}""")

        return

    def at_base(self):
        return self.x == 0 and self.y == 0

    def update_known_map(self):
        if [self.x, self.y] not in self.known_map:
            self.known_map.append([self.x, self.y])
            discovered = (self.x, self.y)
            self.map_graph[discovered] = []
            for coord in self.map_graph.keys():
                cost = self.is_neighbour(discovered, coord)
                if cost != None:
                    self.map_graph[discovered].append([coord, cost])
                    self.map_graph[coord].append([discovered, cost])

    def is_neighbour(self, coord1, coord2):
        if (coord1[0] - 1, coord1[1]) == coord2:
            return self.COST_LINE
        if (coord1[0], coord1[1] - 1) == coord2:
            return self.COST_LINE
        if (coord1[0] - 1, coord1[1] - 1) == coord2:
            return self.COST_DIAG
        if (coord1[0] + 1, coord1[1]) == coord2:
            return self.COST_LINE
        if (coord1[0], coord1[1] + 1) == coord2:
            return self.COST_LINE
        if (coord1[0] + 1, coord1[1] + 1) == coord2:
            return self.COST_DIAG
        if (coord1[0] + 1, coord1[1] - 1) == coord2:
            return self.COST_DIAG
        if (coord1[0] - 1, coord1[1] + 1) == coord2:
            return self.COST_DIAG
        return None

    def come_back(self):
        base_position = (0, 0)
        path = self.astar(self.map, (self.x, self.y), base_position)
        print(path)
        if path is not None:
            print("Iniciando retorno")
            for position in path:
                dx = position[0] - self.x
                dy = position[1] - self.y
                self.walk(dx, dy)
                self.x += dx
                self.y += dy
                print(f"Agente movido para posição: ({self.x}, {
                      self.y}) Tempo: {self.get_rtime()}")

            if (self.at_base()):
                self.position_stack = []
                print(f"Agente na Base")
                return
        else:
            print("Não foi possível encontrar um caminho para a base.")
            return

    def heuristic(self, a, b):
        return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

    def astar(self, map_instance, start, goal):
        open_set = PriorityQueue()
        open_set.put(start, 0)
        came_from = {}
        g_score = {position: float('inf')
                   for position in map_instance.map_data.keys()}
        g_score[start] = 0
        f_score = {position: float('inf')
                   for position in map_instance.map_data.keys()}
        f_score[start] = self.heuristic(start, goal)

        while not open_set.empty():
            current = open_set.get()

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in self.get_neighbors(map_instance, current):
                # Assuming each move costs 1
                tentative_g_score = g_score[current] + 1

                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + \
                        self.heuristic(neighbor, goal)
                    if neighbor not in open_set.queue:
                        open_set.put(neighbor, f_score[neighbor])

        return None  # No path found

    def get_neighbors(self, map_instance, position):
        neighbors = []
        for action, (dx, dy) in map_instance.coordinates_map.items():
            new_x, new_y = position[0] + dx, position[1] + dy
            if map_instance.is_position_known(new_x, new_y):
                neighbors.append((new_x, new_y))
        return neighbors

    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        self.update_known_map()  # atualizar o mapa que já é conhecido

        consumed_time = self.TLIM - self.get_rtime()
        if consumed_time < self.get_rtime():
            self.explore()
            return True

        # time to come back to the base
        if not self.position_stack or (self.x == 0 and self.y == 0):
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            print(f"""{self.NAME}: rtime {
                self.get_rtime()}, chegou na base""")
            # input(f"{self.NAME}: type [ENTER] to proceed")

            if self.at_base:
                self.resc.combine_maps(self.known_map, self.known_victims)
                # self.resc.go_save_victims(self.map, self.victims)
            return False
        else:
            self.come_back()
            return True

    def authorize(self, obstacles, x, y):
        if x == 0 and y == -1:
            if obstacles[0] == 0:
                return False
        if x == 1 and y == -1:
            if obstacles[1] == 0:
                return False
        if x == 1 and y == 0:
            if obstacles[2] == 0:
                return False
        if x == 1 and y == 1:
            if obstacles[3] == 0:
                return False
        if x == 0 and y == 1:
            if obstacles[4] == 0:
                return False
        if x == -1 and y == 1:
            if obstacles[5] == 0:
                return False
        if x == -1 and y == 0:
            if obstacles[6] == 0:
                return False
        if x == -1 and y == -1:
            if obstacles[7] == 0:
                return False
        return True
