"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

import chess
import chess.engine
import random
from engine_wrapper import EngineWrapper

stockfishPath = "stockfish"


class FillerEngine:
    """
        Not meant to be an actual engine.

        This is only used to provide the property "self.engine"
        in "MinimalEngine" which extends "EngineWrapper
        """

    def __init__(self, main_engine, name=None):
        self.id = {
            "name": name
        }
        self.name = name
        self.main_engine = main_engine

    def __getattr__(self, method_name):
        main_engine = self.main_engine

        def method(*args, **kwargs):
            nonlocal main_engine
            nonlocal method_name
            return main_engine.notify(method_name, *args, **kwargs)

        return method


class MinimalEngine(EngineWrapper):
    """
    Subclass this to prevent a few random errors

    Even though MinimalEngine extends EngineWrapper,
    you don't have to actually wrap an engine.

    At minimum, just implement `search`,
    however you can also change other methods like
    `notify`, `first_search`, `get_time_control`, etc.
    """

    def __init__(self, *args, name=None):
        super().__init__(*args)

        self.engine_name = self.__class__.__name__ if name is None else name

        self.last_move_info = []
        self.engine = FillerEngine(self, name=self.name)
        self.engine.id = {
            "name": self.engine_name
        }

    def search_with_ponder(self, board, wtime, btime, winc, binc, ponder):
        timeleft = 0
        if board.turn:
            timeleft = wtime
        else:
            timeleft = btime
        return self.search(board, timeleft, ponder)

    def search(self, board, timeleft, ponder):
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        """
        The EngineWrapper class sometimes calls methods on "self.engine".
        "self.engine" is a filler property that notifies <self> 
        whenever an attribute is called.

        Nothing happens unless the main engine does something.

        Simply put, the following code is equivalent
        self.engine.<method_name>(<*args>, <**kwargs>)
        self.notify(<method_name>, <*args>, <**kwargs>)
        """
        pass


class ExampleEngine(MinimalEngine):
    pass


# Strategy names and ideas from tom7's excellent eloWorld video

class RandomMove(ExampleEngine):
    def search(self, board, *args):
        return random.choice(list(board.legal_moves))


class Alphabetical(ExampleEngine):
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return moves[0]


class FirstMove(ExampleEngine):
    """Gets the first move when sorted by uci representation"""

    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return moves[0]


class Anarchy(ExampleEngine):

    def __init__(self, *args):
        self.stockfish = chess.engine.SimpleEngine.popen_uci(stockfishPath)
        super().__init__(*args)

    def evaluate(self, board, timeLimit=0.1):
        result = self.stockfish.analyse(
            board, chess.engine.Limit(time=timeLimit - 0.01))
        return result["score"].relative

    def search(self, board: chess.Board, timeLeft, *args):

        # Get amount of legal moves
        legalMoves = tuple(board.legal_moves)

        # Base search time per move in seconds
        searchTime = 0.1

        # If the engine will search for more than 10% of the remaining time, then shorten it
        # to be 10% of the remaining time
        # Also, don't do this on the first move (because of weird behavior with timeLeft being a Limit on first move)
        if type(timeLeft) != chess.engine.Limit:
            timeLeft /= 1000  # Convert to seconds
            if len(legalMoves) * searchTime > timeLeft / 10:
                searchTime = (timeLeft / 10) / len(legalMoves)

        # Initialise variables
        bestEvaluation = None
        bestMove = None

        # Evaluate each move
        for move in legalMoves:

            # en passant is forced
            if (board.is_en_passant(move)):
                print("en passant is forced")
                return move

            # play the ruy lopez
            if board.board_fen() == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR":
                print("e4 best by test")
                return "e2e4"

            if board.board_fen() == "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR":
                return "g1f3"

            if board.board_fen() == "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R":
                return "f1b5"

            # always play the bongcloud
            if board.san(move) == "Ke2" or board.san(move) == "Ke7" or board.san(move) == "Kxe2" or board.san(move) == "Kxe7":
                return move

            # never play rook a4
            if not (board.san(move)[0] == "R" and board.san(move)[-2:] == "a4"):

                # play move
                board.push(move)
                # evaluate position
                evaluation = self.evaluate(board, searchTime)
                # if the evaluation is better than the current position use it as the new best move
                if bestEvaluation is None or bestEvaluation > evaluation:
                    bestEvaluation = evaluation
                    bestMove = move
                board.pop()
            else:
                print("I saw Ra4, I just didn't like it")

        return bestMove

    def quit(self):
        self.stockfish.close()
