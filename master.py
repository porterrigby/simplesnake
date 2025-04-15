import numpy as np
from clemcore.clemgame import GameSpec, GameMaster, GameBenchmark, GameScorer, Player, DialogueGameMaster
from clemcore.backends.model_registry import Model
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


class Navigator(Player):
    def __init__(self, model: Model):
        super().__init__(model)

    def _custom_response(self, context):
        return f"<MOVE: UP>"


class Describer(Player):
    def __init__(self, model: Model):
        super().__init__(model)

    def _custom_response(self, context):
        return "[][][*]\n[][][]\n[][s][]"


class SimpleSnake(DialogueGameMaster):
    """ Implements a game of snake in which one player describes the directions in which
    to move a snake within a grid to find its food.
    """
    
    def __init__(self, game_name: str, game_path: str, experiment: Dict, player_models: List[Model] = None):
        super().__init__(game_name, game_path, experiment, player_models)
        # READ IN SETTINGS FROM EXPERIMENT/INSTANCE.JSON???
        self.max_turns = experiment['max_turns']
        self.describer_initial_prompt = experiment['describer_initial_prompt']
        self.navigator_initial_prompt = experiment['navigator_initial_prompt']
        self.describer_tag = experiment['describer_tag']
        self.navigator_tag = experiment['navigator_tag']

    def _on_setup(self, **game_instance):
        # describer should be the programmatic player?
        self.navigator = Navigator(self.player_models[0])
        self.add_player(self.navigator)
        # self.describer = Describer(self.player_models[1])
        # self.add_player(self.describer)

        self.gameboard = [[None] for _ in range(9)]
        self.invalid_response = False
        self.invalid_format = False

        self.game_instance = game_instance
        self.snake_location = game_instance['snake_start_loc']
        self.prey_location = game_instance['prey_start_loc']

    def _on_before_game(self):
        self.set_context_for(player=self.navigator, content=self.navigator_initial_prompt)

    def _does_game_proceed(self):
        """Proceed as long as the snake does not occupy the same gridspace as the prey."""
        if self.invalid_response:
            self.log_to_self("invalid response", "abort game")
            return False
        if self.invalid_format:
            self.log_to_self("invalid format", "abort game")
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
            # is navigator response in valid format?    
            if not (utterance.startswith(f'<move:') and utterance.endswith('>')):
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
