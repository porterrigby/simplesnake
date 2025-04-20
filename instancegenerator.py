import os
import random
import logging
from clemcore.clemgame import GameInstanceGenerator

MAX_TURNS = 15
N_INSTANCES = 10
GAME_NAME = 'simplesnake'
SEED = -413  # spring, gymnopedie, air :)

logger = logging.getLogger(__name__)

LANGUAGE = "en"


class SimpleSnakeInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        super().__init__(os.path.dirname(__file__))

    def on_generate(self):
        print("current path:", self.game_path)
        matrices = self.load_file('resources/matrices.txt').strip('\n').split('\n')

        for matrix in matrices:
            experiment = self.add_experiment(matrix)
            dim = int(matrix[0])
            experiment['dim'] = dim
            experiment['max_turns'] = MAX_TURNS
            experiment['navigator_initial_prompt'] = self.load_template('resources/initial_prompts/navigator_prompt')

            instances = []
            for game_id in range(N_INSTANCES):
                instance = self.add_game_instance(experiment, game_id)

                snake_start_loc = random.choice(range(dim * dim - 1))
                instance['snake_start_loc'] = snake_start_loc

                possible_prey_locs = list(range(dim * dim - 1))
                possible_prey_locs.remove(snake_start_loc)
                prey_start_loc = random.choice(possible_prey_locs)
                instance['prey_start_loc'] = prey_start_loc
                # navigator response pattern (some regex here?)
                # instance['navigator_response_pattern'] =
                instances.append(instance)

            experiment['game_instances'] = instances


if __name__ == '__main__':
    random.seed(SEED)
    SimpleSnakeInstanceGenerator().generate()
            