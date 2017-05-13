# -*- coding:utf-8 -*-  
import argparse, copy, signal, sys, timeit, imp, traceback
from board import Board, move_string, print_moves

player = {-1 : "Black", 1 : "White"}

def game(white_engine, black_engine, game_time=60.0, verbose=False):
    """ Run a single game. Raise RuntimeError in the event of time expiration.
    Raise LookupError in the case of a bad move. The tournament engine must
    handle these exceptions. """

    # Initialize variables
    board = Board()
    totaltime = { -1 : game_time*60, 1 : game_time*60 }
    engine = { -1 : black_engine, 1 : white_engine }

    if verbose:
        print "INITIAL BOARD\n--\n"
        board.display(totaltime)

    # Do rounds 
    # 每方最多走60次
    for move_num in range(60):
        moves = []
        for color in [-1, 1]:
            start_time = timeit.default_timer()
            move = get_move(board, engine[color], color, move_num, totaltime)
            end_time = timeit.default_timer()
            # Update user totaltime
            time = round(end_time - start_time, 1)
            totaltime[color] -= time

            if time > game_time or totaltime[color] < 0:
                raise RuntimeError(color)

            # Make a move, otherwise pass
            if move is not None:
                board.execute_move(move, color)
                moves.append(move)

                if verbose:
                    print "--\n"
                    print "Round " + str(move_num + 1) + ": " + player[color] + " plays in " + move_string(move) + '\n'
                    board.display(totaltime)

        if not moves:
            # No more legal moves. Game is over.
            break

    print "FINAL BOARD\n--\n"
    board.display(totaltime)

    return board

def get_move(board, engine, color, move_num, time, **kwargs):
    """ Get the move for the given engine and color. Check validity of the
    move. """
    legal_moves = board.get_legal_moves(color)

    if not legal_moves:
        return None
    elif len(legal_moves) == 1:
        return legal_moves[0]
    else:
        try:
            move = engine.get_move(copy.deepcopy(board), color, move_num, time[color], time[-color])
        except Exception, e:
            print traceback.format_exc()
            raise SystemError(color)

        if move not in legal_moves:
            print "legal list", [move_string(m) for m in legal_moves]
            print "illegal", move_string(move), "=", move
            raise LookupError(color)

        return move

def winner(board):
    """ Determine the winner of a given board. Return the points of the two
    players. """
    black_count = board.count(-1)
    white_count = board.count(1)
    if black_count > white_count:
        #if black_count + white_count != 64:
        #    black_count += (64 - black_count - white_count)
        return (-1, black_count, white_count)
    elif white_count > black_count:
        #if black_count + white_count != 64:
        #    white_count += (64 - black_count - white_count)
        return (1, black_count, white_count)
    else:
        return (0, black_count, white_count)

def signal_handler(signal, frame):
    """ Capture SIGINT command. """
    print '\n\n- You quit the game!'
    sys.exit()

result = (0, 0, 0)

TRIAL = 10
def main(white_engine, black_engine, game_time, verbose):
    try:
        wwins = ties = bwins = 0

        player[-1] = player[-1][:-8]
        player[1] = player[1][:-8]

        for i in range(int(TRIAL/2)):
            print "NEW GAME"
            print "White:", player[1]
            print "Black:", player[-1]
            board = game(white_engine, black_engine, game_time, verbose)
            stats = winner(board)
            bscore = str(stats[1])
            wscore = str(stats[2])
            if stats[0] == -1:
                bwins += 1
                print "- " + player[-1] + " wins the game! (" + bscore + "-" + wscore + ")"
            elif stats[0] == 1:
                wwins += 1
                print "- " + player[1] + " wins the game! (" + wscore + "-" + bscore + ")"
            else:
                ties += 1
                print "- " + player[-1] + " and " + player[1] + " are tied! (" + bscore + "-" + wscore + ")"
            print '{:<10}{:d}'.format(player[1], wwins)
            print '{:<10}{:d}'.format(player[-1], bwins)
            print '{:<10}{:d}'.format("Ties", ties)

        for i in range(int(TRIAL/2), TRIAL):
            print "NEW GAME"
            print "White:", player[-1]
            print "Black:", player[1]
            board = game(black_engine, white_engine, game_time, verbose)
            stats = winner(board)
            bscore = str(stats[1])
            wscore = str(stats[2])
            if stats[0] == -1:
                wwins += 1
                print "- " + player[1] + " wins the game! (" + bscore + "-" + wscore + ")"
            elif stats[0] == 1:
                bwins += 1
                print "- " + player[-1] + " wins the game! (" + wscore + "-" + bscore + ")"
            else:
                ties += 1
                print "- " + player[1] + " and " + player[-1] + " are tied! (" + bscore + "-" + wscore + ")"
            print '{:<10}{:d}'.format(player[1], wwins)
            print '{:<10}{:d}'.format(player[-1], bwins)
            print '{:<10}{:d}'.format("Ties", ties)

        print "========== FINAL REPORT =========="
        print '{:<10}{:d}'.format(player[1], wwins)
        print '{:<10}{:d}'.format(player[-1], bwins)
        print '{:<10}{:d}'.format("Ties", ties)

        return None

    except RuntimeError, e:
        if e[0] == -1:
            print "\n- " + player[-1] + " ran out of time!"
            print player[1] + " wins the game! (64-0)"
            return (1, 0, 64)
        else:
            print "\n- " + player[1] + " ran out of time!"
            print player[-1] + " wins the game! (64-0)"
            return (-1, 64, 0)

    except LookupError, e:
        if e[0] == -1:
            print "\n- " + player[-1] + " made an illegal move!"
            print player[1] + " wins the game! (64-0)"
            return (1, 0, 64)
        else:
            print "\n- " + player[1] + " made an illegal move!"
            print player[-1] + " wins the game! (64-0)"
            return (-1, 64, 0)

    except SystemError, e:
        if e[0] == -1:
            print "\n- " + player[-1] + " ended prematurely because of an error!"
            print player[1] + " wins the game! (64-0)"
            return (1, 0, 64)
        else:
            print "\n- " + player[1] + " ended prematurely because of an error!"
            print player[-1] + " wins the game! (64-0)"
            return (-1, 64, 0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    # Automatically generate help and usage messages.
    # Issue errors when users gives the program invalid arguments.
    parser = argparse.ArgumentParser(description="Play the Othello game with different engines.")
    parser.add_argument("-black_engine", type=str, nargs=1, help="black engine (human, eona, greedy,lowes, nonull, random)")
    parser.add_argument("-white_engine", type=str, nargs=1, help="white engine (human, eona, greedy,lowes, nonull, random)")
    parser.add_argument("-mB", action="store_true", help="turn on alpha-beta pruning for the black player")
    parser.add_argument("-mW", action="store_true", help="turn on alpha-beta pruning for the white player")
    parser.add_argument("-t", type=int, action="store", help="adjust time limit", default=60)
    parser.add_argument("-v", action="store_true", help="display the board on each turn")
    args = parser.parse_args()

    black_engine = args.black_engine[0]
    white_engine = args.white_engine[0]
    # Retrieve player names
    player[-1] = black_engine + " (black)"
    player[1] = white_engine + " (white)"

    try:
        engines_b = __import__('engines.' + black_engine)
        engines_w = __import__('engines.' + white_engine)
        engine_b = engines_b.__dict__[black_engine].__dict__['engine']()
        engine_w = engines_w.__dict__[white_engine].__dict__['engine']()

        if (black_engine != "greedy" and black_engine != "human" and black_engine != "random"):
            engine_b.alpha_beta = not args.mB
        if (white_engine != "greedy" and white_engine != "human" and white_engine != "random"):
            engine_w.alpha_beta = not args.mW

        v = (args.v or white_engine == "human" or black_engine == "human")
        print player[-1] + " vs. " + player[1] + "\n"
        main(engine_w, engine_b, game_time=args.t, verbose=v)

    except ImportError, e:
        print 'Unknown engine -- ' + e[0].split()[-1]
        sys.exit()
