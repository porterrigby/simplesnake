import random
import string
from clemcore.clemgame.instances import GameInstanceGenerator


GAME_NAME = 'simplesnake'
N_INSTANCES = 10
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

                snake_start_loc = random.choice(range(9))
                prey_start_loc = random.choice(list(range(9)).remove(snake_start_loc))

                n_turns = 15

                instance = self.add_game_instance(experiment, game_id)

                instance['snake_start_loc'] = snake_start_loc
                instance['prey_start_loc'] = prey_start_loc
                instance['n_turns'] = n_turns
                instace['initial_prompt'] = self.create_prompt(
                    matrix, 
                    initial_prompt,
                    snake_start_loc,
                    prey_start_loc,
                    n_turns
                )

    def create_prompt(matrix, prompt, snake_start_loc, prey_start_loc, n_turns) -> str:
        text = string.Template(
            prompt
        ).substitute(
            matrix=matrix, 
            snake_start_loc=snake_start_loc,
            prey_start_loc=prey_start_loc,
            n_turns=n_turns
        )

        return text

if __name__ == '__main__':
    random.seed(SEED)
    SnakeInstanceGenerator().generate()
            t GameInstanceGenerator
import random
import string
from clemcore.clemgame.instances import GameInstanceGenerator


GAME_NAME = 'simplesnake'
N_INSTANCES = 10
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

                snake_start_loc = random.choice(range(9))
                prey_start_loc = random.choice(list(range(9)).remove(snake_start_loc))

                n_turns = 15

                instance = self.add_game_instance(experiment, game_id)

                instance['snake_start_loc'] = snake_start_loc
                instance['prey_start_loc'] = prey_start_loc
                instance['n_turns'] = n_turns
                instace['initial_prompt'] = self.create_prompt(
                    matrix, 
                    initial_prompt,
                    snake_start_loc,
                    prey_start_loc,
                    n_turns
                )

    def create_prompt(matrix, prompt, snake_start_loc, prey_start_loc, n_turns) -> str:
        text = string.Template(
            prompt
        ).substitute(
            matrix=matrix, 
            snake_start_loc=snake_start_loc,
            prey_start_loc=prey_start_loc,
            n_turns=n_turns
        )

        return text

if __name__ == '__main__':
    random.seed(SEED)
    SnakeInstanceGenerator().generate()
            
import random
import string
from clemcore.clemgame.instances import GameInstanceGenerator


GAME_NAME = 'simplesnake'
N_INSTANCES = 10
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

                snake_start_loc = random.choice(range(9))
                prey_start_loc = random.choice(list(range(9)).remove(snake_start_loc))

                n_turns = 15

                instance = self.add_game_instance(experiment, game_id)

                instance['snake_start_loc'] = snake_start_loc
                instance['prey_start_loc'] = prey_start_loc
                instance['n_turns'] = n_turns
                instace['initial_prompt'] = self.create_prompt(
                    matrix, 
                    initial_prompt,
                    snake_start_loc,
                    prey_start_loc,
                    n_turns
                )

    def create_prompt(matrix, prompt, snake_start_loc, prey_start_loc, n_turns) -> str:
        text = string.Template(
            prompt
        ).substitute(
            matrix=matrix, 
            snake_start_loc=snake_start_loc,
            prey_start_loc=prey_start_loc,
            n_turns=n_turns
        )

        return text

if __name__ == '__main__':
    random.seed(SEED)
    SnakeInstanceGenerator().generate()
            