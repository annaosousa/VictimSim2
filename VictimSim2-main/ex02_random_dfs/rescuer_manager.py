from rescuer import Rescuer
from physical_agent import PhysAgent
from kmeans import KMeans
from constants import VS
import csv

class RescuerManager(Rescuer):
    
    cluster_flag = False

    def __init__(self, env, config_file):
        super().__init__(env, config_file)

        self.rescuers = []
        self.explores = []

    def define_rescuers_and_explores(self, list_rescuers, list_explores):
        self.rescuers = list_rescuers
        self.explores = list_explores

    def explorers_finished(self):

        for explorer in self.explores:
            if explorer.get_state() == VS.ACTIVE:
                return False

        return True

    def rescues_finished(self):
        # Verifica se todos os resgatadores estão inativos
        return all(rescuer.get_state() != 'ATIVE' for rescuer in self.rescuers)

    def notify_rescuers_to_plan(self):

        super().__planner()

        # Notifica e planeja as ações de cada resgatador individualmente
        for rescuer in self.rescuers:
            rescuer.wake_up()
            rescuer.receive_map(self.known_map)
            # Planeja as ações do resgatador
            rescuer.__planner()

    def combine_maps(self, path, victims):
        # self.know_map.update(path)
        # self.know_victims.update(victims)

        for i, coord in enumerate(path):
            if coord not in self.known_map:
                self.known_map.append(coord)

        for i, victim in enumerate(victims):
            if victim not in self.known_victims:
                self.known_victims.append(victim)

        for rescuer in self.rescuers:
            rescuer.go_save_victims(self.known_map, self.known_victims)
            
    def clusterize(self):
    #    print("Clusterizando...")
        cluster = KMeans()
        groups = cluster.execute(self.known_victims, 4)
        Rescuer.rescuers_known_victims = self.known_victims.copy()

        for i, rescuer in enumerate(self.rescuers):
            rescuer.set_group(groups[i])
            self.write_group_csv(groups[i], i + 1)

        self.set_group(groups[len(groups) - 1])
        self.write_group(groups[len(groups) - 1], len(groups))

        Rescuer.cluster_flag = True
    
    def write_group(self, group, group_number):
        # Nome do arquivo CSV
        filename = f'cluster{group_number}.txt'

        # Abre o arquivo e cria um CSV writer
        with open(filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')

            # Salva a informação no arquivo CSV
            for row in group[1]:
                csv_writer.writerow([row[1][0], row[0][0], row[0][1], row[1][1], row[1][2]])

        print(f'Informação salva em {filename}')
    
    def deliberate(self) -> bool:
        """ This is the choice of the next action. The simulator calls this
        method at each reasonning cycle if the agent is ACTIVE.
        Must be implemented in every agent
        @return True: there's one or more actions to do
        @return False: there's no more action to do """
        
        if Rescuer.cluster_flag == False:

            if self.explorers_finished():
                self.clusterize()
                self.notify_rescuers_to_plan()
            else:
                return True
            
        # No more actions to do
        if self.plan == []:  # empty list, no more actions to do
            if self.rescuers_finished():
                return False
            else:
                return True

        return True

