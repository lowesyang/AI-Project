"""
Jaimie Murdock
September 17, 2011

Abstract class for an Othello game engine.
"""

class Engine(object):
    """ Abstract class for an Othello game engine. """
    def get_black_move(self, board, move_num=None,
                       time_remaining=None, time_opponent=None):
        """ Return the black player's move, given a board.
        Call self.get_move(board, -1) by default. """
        raise DeprecationWarning
        return self.get_move(board, -1, move_num,
                             time_remaining, time_opponent)

    def get_white_move(self, board, move_num=None,
                       time_remaining=None, time_opponent=None):
        """ Return the white player's move, given a board.
        Call self.get_move(board, +1) by default. """
        raise DeprecationWarning
        return self.get_move(board, 1, move_num,
                             time_remaining, time_opponent)

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        """ Placeholder for the actual engine. Any subclass must implement this
        method or otherwise raise a NotImplementedError. """
        raise NotImplementedError
