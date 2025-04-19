import re
import numpy as np
from clemcore.clemgame import GameSpec, GameMaster, GameBenchmark, GameScorer, Player, DialogueGameMaster
from clemcore.backends.model_registry import Model, CustomResponseModel
from typing import Dict, List
from clemcore.clemgame.metrics import METRIC_REQUEST_COUNT_VIOLATED, METRIC_REQUEST_COUNT_PARSED, METRIC_REQUEST_COUNT, \
                                        METRIC_REQUEST_SUCCESS, METRIC_ABORTED, BENCH_SCORE, METRIC_SUCCESS, METRIC_LOSE
import logging
logger = logging.getLogger(__name__)


class SimpleSnakeGameBenchmark(GameBenchmark):
    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    def get_description(self):
        return "Plays a simple game of snake with one player."

    def is_single_player(self) -> bool:
        return True

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> GameMaster:
        return SimpleSnake(self.game_name, self.game_path, experiment, player_models)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return SimpleSnakeGameScorer(self.game_name, experiment, game_instance)


class Gameboard:
    def __init__(self, dim, snake_start_loc, prey_start_loc):
        self.gameboard = [['' for _ in range(dim)] for _ in range(dim)]
        self.dim = dim

        # set snake start location
        self.snake_pos = [snake_start_loc // dim, snake_start_loc % dim]
        self.gameboard[self.snake_pos[0]][self.snake_pos[1]] = 's'

        # set prey start location
        self.prey_pos = [prey_start_loc // dim, prey_start_loc % dim]
        self.gameboard[prey_start_loc // dim][prey_start_loc % dim] = '*'

    def update_gameboard(self, new_loc) -> str:
        """Updates the snake location on the gameboard. Returns True if
        update results in valid game state, otherwise False.
        """
        row, col = new_loc
        # check game state
        if row == self.prey_pos[0] and col == self.prey_pos[1]:
            return 'win state'
        if (row < 0 or row >= self.dim) or (col < 0 or col >= self.dim):
            return 'invalid state'

        # move doesn't end game, so update snake pos
        self.gameboard[self.snake_pos[0]][self.snake_pos[1]] = ''
        self.snake_pos[0], self.snake_pos[1] = row, col
        self.gameboard[self.snake_pos[0]][self.snake_pos[1]] = 's'
        return self.__str__()

    def __str__(self):
        result = ''
        for row in self.gameboard:
            for col in row:
                result += f'[{col}]'

            if row != self.gameboard[-1]:
                result += '\n'
        return result


class Navigator(Player):
    def __init__(self, model: Model):
        super().__init__(model)

    def _custom_response(self):
        return "Alright, I'm ready!"


class Describer(Player):
    def __init__(self, dim, snake_start_loc, prey_start_loc):
        super().__init__(CustomResponseModel())
        self.gameboard = Gameboard(dim, snake_start_loc, prey_start_loc)
        self.init_game_state = True

    def _custom_response(self, context: Dict) -> str:
        if self.init_game_state:
            self.init_game_state = False
            return self.gameboard.__str__()

        # parse direction and determine new snake location
        pattern = r'<move:\s*(up|down|left|right)>'
        match = re.search(pattern, context['content'].lower())
        direction = match.group(1)

        if direction == 'up':
            row = self.gameboard.snake_pos[0] - 1
            col = self.gameboard.snake_pos[1]
        elif direction == 'down':
            row = self.gameboard.snake_pos[0] + 1
            col = self.gameboard.snake_pos[1]
        elif direction == 'left':
            row = self.gameboard.snake_pos[0]
            col = self.gameboard.snake_pos[1] - 1
        elif direction == 'right':
            row = self.gameboard.snake_pos[0]
            col = self.gameboard.snake_pos[1] + 1
        else:
            raise RuntimeError('Failed to parse direction.')

        return self.gameboard.update_gameboard((row, col))


class SimpleSnake(DialogueGameMaster):
    """ Implements a game of snake in which one player describes the directions in which
    to move a snake within a grid to find its food.
    """
    
    def __init__(self, game_name: str, game_path: str, experiment: Dict, player_models: List[Model] = None):
        super().__init__(game_name, game_path, experiment, player_models)
        # experiment-level variables
        self.max_turns = experiment['max_turns']
        self.dim = experiment['dim']
        self.navigator_initial_prompt = experiment['navigator_initial_prompt']

    def _on_setup(self, **game_instance):
        # instance-level flags
        self.invalid_response = False
        self.invalid_format = False

        # instance-level variables
        self.game_instance = game_instance
        self.snake_location = game_instance['snake_start_loc']
        self.prey_location = game_instance['prey_start_loc']

        # instance players
        self.navigator = Navigator(self.player_models[0])
        self.add_player(self.navigator)
        self.describer = Describer(self.dim, self.snake_location, self.prey_location)
        self.add_player(self.describer)

    def _on_before_game(self):
        # self.set_context_for(self.describer, 'game start')
        self.set_context_for(self.navigator, self.navigator_initial_prompt)

    def _does_game_proceed(self):
        """Proceed as long as the snake does not occupy the same gridspace as the prey."""
        if self.invalid_response:
            self.log_to_self("invalid response", "abort game")
            return False
        if self.invalid_format:
            self.log_to_self("invalid format", "abort game")
            return False
        if self.win_state:
            self.log_to_self("game win", "end game")
            return False
        if self.invalid_state:
            self.log_to_self("game over", "end game")
            return False
        if self.current_round >= self.max_turns:
            self.log_to_self("max turns reached", str(self.max_turns))
            return False
        return True

    def _validate_player_response(self, player: Player, utterance: str) -> bool:
        # reset flags
        self.invalid_response = False
        self.invalid_format = False
        self.win_state = False
        self.invalid_state = False

        if player == self.navigator:
            if self.current_round == 0:  # ensure grid is sent during initial round
                self.log_to_self("game start", "Get initial grid.")
                return True

            # is navigator response in valid format?    
            pattern = r'<move:\s*(up|down|left|right)>'
            matches = re.findall(pattern, utterance.lower())

            if len(matches) == 0 or len(matches) > 1:
                self.log_to_self("invalid format", "Invalid response.")
                self.invalid_format = True
                return False
        elif player == self.describer:
            # handle end-of-game describer response
            if utterance == 'invalid state':
                self.log_to_self("invalid state", "Game over.")
                self.invalid_state = True
                return False
            if utterance == 'win state':
                self.log_to_self("win state", "Game win.")
                self.win_state = True
                return False

        return True # valid response

    def _on_valid_player_response(self, player: Player, parsed_response: str):
        if player == self.navigator:
            self.set_context_for(self.describer, parsed_response)
        elif player == self.describer:
            self.set_context_for(self.navigator, parsed_response)


class SimpleSnakeGameScorer(GameScorer):
    """GameScorer subclass for SimpleSnake.
    Reads episode records, counts failures, calculates scores and stores the
    results in score files."""

    def __init__(self, game_name: str, experiment: Dict, game_instance: Dict):
        super().__init__(game_name, experiment, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        """Episode level scores.
        Writes to score file in the episode directory.
        """
        turn_scores = []
        invalid_response_count = 0
        invalid_format_count = 0
        win_state = False
        invalid_state = False
        max_turns = self.experiment['max_turns']
        speed_score = 0

        for turn_idx, turn in enumerate(episode_interactions['turns']):
            turn_score = { 'request_count': 1 }
            invalid_format_in_turn = False
            invalid_response_in_turn = False

            for event_idx, event in enumerate(turn):
                action = event['action']

                if action['type'] == 'invalid format':
                    if event_idx - 1 >= 0:
                        previous_event = turn[event_idx - 1]
                        if previous_event['from'] == 'Player 1':  # navigator
                            invalid_format_count += 1
                    invalid_format_in_turn = True
                elif action['type'] == 'invalid response':
                    if event_idx - 1 >= 0:
                        previous_event = turn[event_idx - 1]
                        if previous_event['from'] == 'Player 1':
                            invalid_response_count += 1
                    invalid_response_in_turn = True
                elif action['type'] == 'game win':
                    win_state = True
                elif action['type'] == 'game over':
                    invalid_state = True
                elif action['type'] == 'max turns reached':  # what should actually happen here?
                    invalid_state = True
                    # raise NotImplementedError

                if invalid_format_in_turn or invalid_response_in_turn:
                    turn_score['violated_request_count'] = 1
                    turn_score['parsed_request_count'] = 0
                else:
                    turn_score['violated_request_count'] = 0
                    turn_score['parsed_request_count'] = 1

                # self.log_turn_score(turn_idx, 'Accuracy', 1 if win_state else 0)
                self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_VIOLATED, turn_score['violated_request_count'])
                self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_PARSED, turn_score['parsed_request_count'])
                self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT, turn_score['request_count'])
                turn_scores.append(turn_score)

            violated_request_count = sum(turn['violated_request_count'] for turn in turn_scores)
            self.log_episode_score(METRIC_REQUEST_COUNT_VIOLATED, violated_request_count)

            parsed_request_count = sum(turn['parsed_request_count'] for turn in turn_scores)
            self.log_episode_score(METRIC_REQUEST_COUNT_PARSED, parsed_request_count)

            request_count = sum(turn['request_count'] for turn in turn_scores)
            self.log_episode_score(METRIC_REQUEST_COUNT, request_count)

            if request_count != 0:
                self.log_episode_score(METRIC_REQUEST_SUCCESS, parsed_request_count / request_count)
            else:
                self.log_episode_score(METRIC_REQUEST_SUCCESS, 0)

            if invalid_format_in_turn or invalid_response_in_turn:
                self.log_episode_score(METRIC_ABORTED, 1)
                self.log_episode_score(BENCH_SCORE, np.nan)
            else:
                self.log_episode_score(METRIC_ABORTED, 0)

                if win_state:
                    self.log_episode_score(METRIC_SUCCESS, 1)
                    self.log_episode_score(METRIC_LOSE, 0)

                    # compute speed score here
                    speed_score = 100 * (max_turns - request_count) / max_turns
                    bench_score = max(0, speed_score)
                    self.log_episode_score('Speed', bench_score)
                else:
                    self.log_episode_score(METRIC_SUCCESS, 0)
                    self.log_episode_score(METRIC_LOSE, 1)
                    self.log_episode_score(BENCH_SCORE, 0)

            self.log_episode_score("Invalid format from navigator", invalid_format_count)
            self.log_episode_score("Invalid response from navigator", invalid_response_count)
