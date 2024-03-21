import sys
import os
import time

# importa classes
from environment import Env
from explorer import Explorer
from rescuer import Rescuer
from rescuer_manager import RescuerManager


def main(data_folder_name):

    # Set the path to config files and data files for the environment
    current_folder = os.path.abspath(os.getcwd())
    data_folder = os.path.abspath(
        os.path.join(current_folder, data_folder_name))

    # Instantiate the environment
    env = Env(data_folder)

    # config files for the agents
    rescuer_file = os.path.join(data_folder, "rescuer_config.txt")
    explorer_file = os.path.join(data_folder, "explorer_config.txt")

    # Instantiate agents rescuer and explorer
    resc_list = []

    resc1 = Rescuer(env, rescuer_file)
    resc_list.append(resc1)
    resc2 = Rescuer(env, rescuer_file)
    resc_list.append(resc2)
    resc3 = Rescuer(env, rescuer_file)
    resc_list.append(resc3)
    resc4 = Rescuer(env, rescuer_file)
    resc_list.append(resc4)
    resc_manager = RescuerManager(env, rescuer_file)

    # Explorer needs to know rescuer to send the map
    # that's why rescuer is instatiated before
    exp_list = []

    exp1 = Explorer(env, explorer_file, resc_manager, [
                    'UP', 'RIGHT', 'DOWN', 'LEFT', 'UP-LEFT', 'DOWN-LEFT', 'UP-LEFT', 'DOWN-LEFT'])
    exp_list.append(exp1)
    exp2 = Explorer(env, explorer_file, resc_manager, [
                    'DOWN', 'LEFT', 'UP', 'RIGHT', 'DOWN-LEFT', 'DOWN-LEFT', 'UP-LEFT', 'UP-LEFT'])
    exp_list.append(exp2)
    exp3 = Explorer(env, explorer_file, resc_manager, [
                    'LEFT', 'DOWN', 'RIGHT', 'UP', 'DOWN-LEFT', 'UP-LEFT', 'DOWN-LEFT', 'UP-LEFT'])
    exp_list.append(exp3)
    exp4 = Explorer(env, explorer_file, resc_manager, [
                    'RIGHT', 'UP', 'LEFT', 'DOWN', 'DOWN-LEFT', 'UP-LEFT', 'UP-LEFT', 'DOWN-LEFT'])
    exp_list.append(exp4)

    resc_manager.define_rescuers_and_explores(resc_list, exp_list)

    # Run the environment simulator
    env.run()


if __name__ == '__main__':
    """ To get data from a different folder than the default called data
    pass it by the argument line"""

    if len(sys.argv) > 1:
        data_folder_name = sys.argv[1]
    else:
        data_folder_name = os.path.join("datasets", "data_10v_12x12")

    main(data_folder_name)
