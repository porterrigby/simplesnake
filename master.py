from clemcore.clemgame import GameSpec, GameMaster, GameBenchmark, Player, DialogueGameMaster
from clemcore.backends.model_registry import Model
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class SnakeGameBenchmark(GameBenchmark):
    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    def get_description(self):
        return "Plays a simple game of snake with one player."

    def is_single_player(self) -> bool:
        return True

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> GameMaster:
        return Snake(self.game_name, self.game_path, experiment, player_models)


class Navigator(Player):
    def __init__(self, model: Model):
        super().__init__(model)

    def _custom_response(self, context):
        return f"<MOVE UP>"


class Describer(Player):
    def __init__(self, model: Model):
        super().__init__(model)

    def _custom_response(self, context):
        return "[][][*]\n[][][]\n[][s][]"
    
class Snake(DialogueGameMaster):
    """ Implements a game of snake in which one player describes the directions in which
    to move a snake within a grid to find its food.
    """
    
    def __init__(self, game_name: str, game_path: str, experiment: Dict, player_models: List[Model] = None):
        super().__init__(game_name, game_path, experiment, player_models)
        # READ IN SETTINGS FROM EXPERIMENT/INSTANCE.JSON???

    def _on_setup(self, **game_instance):
        # describer should be the programmatic player?
        self.navigator = Navigator(self.player_models[0])
        self.add_player(self.navigator)
        self.describer = Describer(self.player_models[1])
        self.add_player(self.describer)

        self.gameboard = [[None] for _ in range(9)]
        self.invalid_response = False

        self.game_instance = game_instance
        self.max_turns = game_instance['max_turns']
        self.snake_location = game_instance['snake_start_loc']
        self.prey_location = game_instance['prey_start_loc']
        self.describer_tag = game_instance['describer_tag']
        self.navigator_tag = game_instance['navigator_tag']
        self.describer_initial_prompt = game_instance['describer_initial_prompt']
        self.navigator_initial_prompt = game_instance['navigator_initial_prompt']

    def _on_before_game(self):
        self.set_context_for(self.navigator, self.navigator_initial_prompt)

    def _does_game_proceed(self):
        """Proceed as long as the snake does not occupy the same gridspace as the prey."""
        if self.invalid_response:
            self.log_to_self("invalid response", "abort game")
            return False
        if self.win_state:
            self.log_to_self("game win", "end game")
            return False
        if self.invalid_state:
            self.log_to_self("game over", "end game")
            return False
        if self.current_turn >= self.max_turns:
            self.log_to_self("max turns reached", str(self.max_turns))
            return False
        return True

    def _validate_player_response(self, player: Player, utterance: str) -> bool:

        self.invalid_response = False
        self.win_state = False
        self.invalid_state = False
        
        if player == self.navigator:
            # is navigator response in valid format?    
            if not (utterance.startswith('<'.append(self.navigator_tag)) and utterance.endswith('>')):
                self.log_to_self("invalid format", "Invalid response.")
                self.invalid_format = True
                return False 
        # if player == self.describer:
            # if 
            #validate response format
            # pass
        else:
            return True

    def _on_valid_player_response(self, player: Player, parsed_response: str):
        if player == self.navigator:
            self.set_context_for(self.describer, parsed_response)
        elif player == self.describer:
            self.set_context_for(self.navigator, parsed_response)
            
