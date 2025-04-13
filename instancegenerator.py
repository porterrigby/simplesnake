import random
import string
from clemcore.clemgame.instances import GameInstanceGenerator

MAX_TURNS = 15
N_INSTANCES = 10
GAME_NAME = 'simplesnake'
SEED = -413  # spring, gymnopedie, air :)


class SnakeInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        super().__init__(GAME_NAME)

    def on_generate(self):
        matrices = self.load_file('resources/matrices.txt').strip('\n').split('\n')
        initial_prompt = self.load_template('resources/initial_prompts/initial_prompt_a')

        for matrix in matrices:
            experiment = self.add_experiment(matrix)

            for game_id in range(N_INSTANCES):
                instance = self.add_game_instance(experiment, game_id)
                
                max_turns = MAX_TURNS
                instance['max_turns'] = max_turns
                
                snake_start_loc = random.choice(range(9))
                instance['snake_start_loc'] = snake_start_loc
                prey_start_loc = random.choice(list(range(9)).remove(snake_start_loc))
                instance['prey_start_loc'] = prey_start_loc

                instance['describer_tag'] = 'MATRIX:'
                instance['navigator_tag'] = 'DIRECTION:'

                # navigator response pattern (some regex here?)
                # instance['navigator_response_pattern'] = 
                
                instance['describer_initial_prompt'] = self.load_template('resources/initial_prompts/describer_prompt')
                instance['navigator_initial_prompt'] = self.load_template('resources/initial_prompts/navigator_prompt')


if __name__ == '__main__':
    random.seed(SEED)
    SnakeInstanceGenerator().generate()
            