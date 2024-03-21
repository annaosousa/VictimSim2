# EXPLORER AGENT
# @Author: Tacla, UTFPR
#
# It walks randomly in the environment looking for victims. When half of the
# exploration has gone, the explorer goes back to the base.

import sys
import os
import random
import math
from abc import ABC, abstractmethod
from abstract_agent import AbstAgent
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

    def get_next_position(self):
        """ Randomically, gets the next position that can be explored (no wall and inside the grid)
            There must be at least one CLEAR position in the neighborhood, otherwise it loops forever.
        """
        # Check the neighborhood walls and grid limits
        # obstacles = self.check_walls_and_lim()

        # # Loop until a CLEAR position is found
        # while True:
        #     # Get a random direction
        #     direction = random.randint(0, 7)
        #     # Check if the corresponding position in walls_and_lim is CLEAR
        #     if obstacles[direction] == VS.CLEAR:
        #         return Explorer.AC_INCR[direction]

        # Check the neighborhood walls and grid limits
        obstacles = self.check_walls_and_lim()

        # Lista de direções possíveis
        directions = list(range(8))
        random.shuffle(directions)  # Embaralha as direções

        # Loop até encontrar uma posição não visitada
        for direction in directions:
            # Verifica a direção correspondente
            dx, dy = Explorer.AC_INCR[direction]
            if obstacles[direction] == VS.CLEAR:
                next_x, next_y = self.x + dx, self.y + dy
                # Verifica se a próxima posição já foi visitada
                if not self.map.is_position_known(next_x, next_y):
                    return dx, dy

        # Se todas as direções levarem a posições conhecidas, retorna 0, 0 (ficar parado)
        return 0, 0

    def explore(self):
        # Check the neighborhood obstacles
        obstacles = self.check_walls_and_lim()

        # get an random increment for x and y
        # mov = self.map.get_action()
        # dy = mov[0]
        # dx = mov[1]

        dx, dy = self.get_next_position()

        while not self.authorize(obstacles, dx, dy):
            mov = self.map.get_action()
            dy = mov[0]
            dx = mov[1]

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
            print(f"{self.NAME}: Wall or grid limit reached at ({
                  self.x + dx}, {self.y + dy})")

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
                print(f"{self.NAME} Victim found at ({self.x}, {
                      self.y}), rtime: {self.get_rtime()}")
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
            print(f"{self.NAME}:at ({self.x}, {self.y}), diffic: {
                  difficulty:.2f} vict: {seq} rtime: {self.get_rtime()}")

        return

    def at_base(self):
        return self.x == 0 and self.y == 0

    def come_back(self):
        dx, dy = self.walk_stack.pop()
        dx = dx * -1
        dy = dy * -1

        result = self.walk(dx, dy)
        if result == VS.BUMPED:
            print(f"{self.NAME}: when coming back bumped at ({
                  self.x+dx}, {self.y+dy}) , rtime: {self.get_rtime()}")
            return

        if result == VS.EXECUTED:
            # update the agent's position relative to the origin
            self.x += dx
            self.y += dy
            print(f"{self.NAME}: coming back at ({self.x}, {
                self.y}), rtime: {self.get_rtime()}")
            if self.walk_stack.is_empty():
                # Se a pilha de movimentos estiver vazia, chama o método combine_maps() do RescuerManager
                self.resc.combine_maps(
                    self.known_map, self.known_victims)

    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        # self.set_known_map()  # atualizar o mapa que já é conhecido

        if self.get_rtime() > self.time_to_comeback:
            self.explore()
            return True
        else:
            # time to come back to the base
            if self.walk_stack.is_empty():
                # time to wake up the rescuer
                # pass the walls and the victims (here, they're empty)
                print(f"{self.NAME}: rtime {
                      self.get_rtime()}, invoking the rescuer")
                input(f"{self.NAME}: type [ENTER] to proceed")
                self.resc.go_save_victims(self.map, self.victims)
                return False
            else:
                self.come_back()
                return True

    # def deliberate(self) -> bool:
    #     """ The agent chooses the next action. The simulator calls this
    #     method at each cycle. Must be implemented in every agent"""

    #     self.set_known_map()  # Adiciona base na lista

    #     if self.time_to_get_back():
    #         # Returns to base and notify the rescuer
    #         # If agent is not at the base, returns True
    #         return self.get_back_to_base()

    #     return self.explore()

    # def set_known_map(self):
    #     if [self.x, self.y] not in self.set_known_map:
    #         self.set_known_map.append([self.x, self.y])
    #         discovered = (self.x, self.y)
    #         self.map_graph[discovered] = []

    #         for coord in self.map_graph.keys():
    #             cost = self.is_neighbour(discovered, coord)
    #             if cost != None:
    #                 self.map_graph[discovered].append([coord, cost])
    #                 self.map_graph[coord].append([discovered, cost])

    # def is_neighbour(self, coord1, coord2):
    #     if (coord1[0] - 1, coord1[1]) == coord2:
    #         return self.COST_LINE
    #     if (coord1[0], coord1[1] - 1) == coord2:
    #         return self.COST_LINE
    #     if (coord1[0] - 1, coord1[1] - 1) == coord2:
    #         return self.COST_DIAG
    #     if (coord1[0] + 1, coord1[1]) == coord2:
    #         return self.COST_LINE
    #     if (coord1[0], coord1[1] + 1) == coord2:
    #         return self.COST_LINE
    #     if (coord1[0] + 1, coord1[1] + 1) == coord2:
    #         return self.COST_DIAG
    #     if (coord1[0] + 1, coord1[1] - 1) == coord2:
    #         return self.COST_DIAG
    #     if (coord1[0] - 1, coord1[1] + 1) == coord2:
    #         return self.COST_DIAG
    #     return None

    def authorize(self, obstacles, x, y):
        if x == 0 and y == -1:
            if obstacles[0] != 0:
                return False
        if x == 1 and y == -1:
            if obstacles[1] != 0:
                return False
        if x == 1 and y == 0:
            if obstacles[2] != 0:
                return False
        if x == 1 and y == 1:
            if obstacles[3] != 0:
                return False
        if x == 0 and y == 1:
            if obstacles[4] != 0:
                return False
        # if x == -1 and y == 1:
        #     if obstacles[5] != 0:
        #         return False
        if x == -1 and y == 0:
            if obstacles[6] != 0:
                return False
        if x == -1 and y == -1:
            if obstacles[7] != 0:
                return False
        return True
