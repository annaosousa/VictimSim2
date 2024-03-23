from rescuer import Rescuer


class RescuerManager(Rescuer):
    def __init__(self, env, config_file):
        super().__init__(env, config_file)

        self.rescuers = []
        self.explorers = []

    def define_rescuers_and_explores(self, rescuers, explores):
        self.rescuers = rescuers
        self.explores = explores

    def explores_finished(self):
        # Verifica se todos os exploradores estão inativos
        return all(explorer.get_state() != 'ATIVE' for explorer in self.explores)

    def rescues_finished(self):
        # Verifica se todos os resgatadores estão inativos
        return all(rescuer.get_state() != 'ATIVE' for rescuer in self.rescuers)

    # def notify_rescuers_to_plan(self):

    #     super().__planner()

    #     # Notifica e planeja as ações de cada resgatador individualmente
    #     for rescuer in self.rescuers:
    #         # Acorda o resgatador
    #         rescuer.wake_up()
    #         # Fornece o mapa conhecido ao resgatador
    #         rescuer.receive_map(self.known_map)
    #         # Planeja as ações do resgatador
    #         # Presumivelmente, esta função incluirá o planejamento com base no mapa conhecido
    #         rescuer.__planner()

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
