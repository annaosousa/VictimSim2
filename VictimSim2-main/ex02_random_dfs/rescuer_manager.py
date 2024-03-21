from rescuer import Rescuer


class RescuerManager(Rescuer):
    def __init__(self, env, config_file):
        super().__init__(env, config_file)

        self.know_map = set()
        self.know_victims = set()

    def define_rescuers_and_explores(self, rescuers, explores):
        self.rescuers = rescuers
        self.explores = explores

    def combine_maps(self, path, victims):
        self.know_map.update(path)
        self.know_victims.update(victims)
