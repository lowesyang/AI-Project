from engines import Engine
from copy import deepcopy

class GreedyEngine(Engine):
    """ Game engine that implements a simple fitness function maximizing the
    difference in number of pieces in the given color's favor. """
    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        """ Return a move for the given color that maximizes the difference in
        number of pieces for that color. """
        # Get a list of all legal moves.
        moves = board.get_legal_moves(color)

        # Return the best move according to our simple utility function:
        # which move yields the largest different in number of pieces for the
        # given color vs. the opponent?
        return max(moves, key=lambda move: self._get_cost(board, color, move))

    def _get_cost(self, board, color, move):
        """ Return the difference in number of pieces after the given move
        is executed. """

        # Create a deepcopy of the board to preserve the state of the actual board
        newboard = deepcopy(board)
        newboard.execute_move(move, color)

        # Count the # of pieces of each color on the board
        num_pieces_op = len(newboard.get_squares(color*-1))
        num_pieces_me = len(newboard.get_squares(color))

        # Return the difference in number of pieces
        return num_pieces_me - num_pieces_op

engine = GreedyEngine
