from __future__ import absolute_import
from __future__ import division
from engines import Engine
import random
import datetime
import math


class MctsEngine(Engine):
    """ Game engine that implements a simple fitness function maximizing the
    difference in number of pieces in the given color's favor. """

    def __init__(self):
        self.alpha_beta = False
        fill_bit_table()
        fill_lsb_table()
        fill_radial_map()
        # initialize the root node,set default cp = 1.timelimit = 10
        self.nPos = Node()
        self.c = 1
        self.tmlmt = 10

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        """ Return a move for the given color that maximizes the difference in
        number of pieces for that color. """

        W, B = to_bitboard(board)

        wb = (W, B) if color > 0 else (B, W)

        #run MCTSearch to get mv
        res = self.MCTSearch(wb[0], wb[1])
        return to_move(res)

    def MCTSearch(self, W, B):
        bo = False

        # stage 1: root node not initialized
        if not self.nPos.bitboard:
            self.nPos.bitboard = (W, B)
            self.nPos.remmap = move_gen(W, B)
        else:
        #stage 4: opponent cannot move
            if self.nPos.bitboard == (W, B):
                bo = True
            else:
        #stage 2: opponent move
                for tmp in self.nPos.trnode:
                    if tmp.bitboard == (W, B):
                        self.nPos = tmp
                        bo = True
                        break
        #stage 3: 1)player cannnot mv 2)not simulated 3)player has only one choice to mv(engine.get_move is not operated)
            if bo == False:
                self.nPos = Node()
                self.nPos.bitboard = (W, B)
                self.nPos.remmap = move_gen(W, B)

        #Update:selection + expansion + simulation + backpropagation
        stime = datetime.datetime.now()
        while (datetime.datetime.now() - stime).seconds < self.tmlmt:
            quality, number = self.UpdateNode(self.nPos)

        #return bestmv
        return self.BestChildmv(self.nPos)

    def UpdateNode(self, pos):
        quality = 0
        number = 0
        if pos.remmap == 0:
            # the node has fully expanded && is nonterminal
            if move_gen(pos.bitboard[0], pos.bitboard[1]) != 0:
                #UCB policy
                max = -float("inf")
                tpos = {}
                for i in pos.trnode:
                    tmp = i.quality / i.number + self.c * math.sqrt(2 * math.log(pos.number) / i.number)
                    if max < tmp:
                        max = tmp
                        tpos = i
                #recursively operate function && backpropagation
                quality, number = self.UpdateNode(tpos)
                pos.quality += quality * pos.user
                pos.number += number
            else:#is terminal , run simulation
                quality, number = self.DefaultPolicy(pos)
                pos.quality += quality * pos.user
                pos.number += number
        else:
            #the node hasn't been fully expanded,expansion && simulation
            newpos = self.expand(pos)
            quality, number = self.DefaultPolicy(newpos)
            newpos.quality += quality * newpos.user
            newpos.number += number
            pos.quality += quality * pos.user
            pos.number += number

        return quality, number

    #choose to expand player's or oppnent's node
    def expand(self, pos):
        #player mv and flip
        mv, pos.remmap = pop_lsb(pos.remmap)
        newpos = Node()
        tmpW, tmpB = pos.bitboard
        flipmask = flip(tmpW, tmpB, mv)
        tmpW ^= flipmask | BIT[mv]
        tmpB ^= flipmask

        #if oppo can move
        newpos.remmap = move_gen(tmpB, tmpW)
        if newpos.remmap != 0:
            newpos.bitboard = (tmpB, tmpW)
            newpos.user  = -pos.color
            newpos.color = -pos.color
            newpos.mv = mv
        #if oppo cannot mv but player can mv
        elif move_gen(tmpW, tmpB)!=0:
            newpos.remmap = move_gen(tmpW, tmpB)
            newpos.bitboard = (tmpW, tmpB)
            newpos.user = -pos.color
            newpos.color = pos.color
            newpos.mv = mv
        #both cannot mv
        else:
            newpos.bitboard = (tmpB, tmpW)
            newpos.user  = -pos.color
            newpos.color = -pos.color
            newpos.mv = mv
        pos.trnode.append(newpos)
        return newpos

    #default policy , choose the same policy as expand
    def DefaultPolicy(self, pos):
        quality = 0
        tmpW, tmpB = pos.bitboard
        b = (pos.color+1)/2
        tmap = move_gen(tmpW, tmpB)
        while tmap !=0 :
            mlist = []
            while tmap != 0:
                mv, tmap = pop_lsb(tmap)
                mlist.append(mv)
            mv = random.choice(mlist)
            flipmask = flip(tmpW, tmpB, mv)
            tmpW ^=  flipmask | BIT[mv]
            tmpB ^=  flipmask

            tmap = move_gen(tmpB, tmpW)
            if tmap !=0:
                tmpW,tmpB = tmpB,tmpW
                b += 1
            else:
                tmap = move_gen(tmpW, tmpB)

        if b %2 == 0:
            score = self.eval(tmpW, tmpB)
        else:
            score = self.eval(tmpB, tmpW)
        if score > 0:
            quality = 1
        elif score< 0:
            quality = -1
        else:
            quality = 0
        return quality, 1

    #return bestchild, choose cp = 0 to run UCB policy
    def BestChildmv(self, pos):
        max = -float("inf")
        tpos = None
        # print "all"
        for i in pos.trnode:
            # print i.quality,i.number
            tmp = i.quality / i.number
            if max < tmp:
                max = tmp
                tpos = i
        self.nPos = tpos
        # print "choose"
        # print tpos.quality,tpos.number
        return tpos.mv


    WEIGHTS = \
        [-3, -7, 11, -4, 8, 1, 2]
    P_RINGS = [0x4281001818008142,
               0x42000000004200,
               0x2400810000810024,
               0x24420000422400,
               0x1800008181000018,
               0x18004242001800,
               0x3C24243C0000]
    P_CORNER = 0x8100000000000081
    P_SUB_CORNER = 0x42C300000000C342

    def eval(self, W, B):
        mycorner = count_bit(W & self.P_CORNER)
        opcorner = count_bit(B & self.P_CORNER)

        # piece difference
        mypiece = mycorner * 100
        for i in range(len(self.WEIGHTS)):
            mypiece += self.WEIGHTS[i] * count_bit(W & self.P_RINGS[i])
        oppiece = opcorner * 100
        for i in range(len(self.WEIGHTS)):
            oppiece += self.WEIGHTS[i] * count_bit(B & self.P_RINGS[i])

        # scorepiece = \
        #             10.0 * mypiece / (mypiece + oppiece) if mypiece > oppiece \
        #             else -10.0 * oppiece / (mypiece + oppiece) if mypiece < oppiece \
        #             else 0
        scorepiece = mypiece - oppiece

        return scorepiece


######-------- bitboard representation -------

class Node():
    def __init__(self):
        self.quality = 0
        self.number = 0
        self.user  = -1
        self.color = -1
        self.mv = None
        self.trnode = []
        self.remmap = None
        self.bitboard = None


def fill_bit_table():
    global BIT
    BIT = [1 << n for n in range(64)]


def move_gen_sub(P, mask, dir):
    dir2 = long(dir * 2)
    flip1 = mask & (P << dir)
    flip2 = mask & (P >> dir)
    flip1 |= mask & (flip1 << dir)
    flip2 |= mask & (flip2 >> dir)
    mask1 = mask & (mask << dir)
    mask2 = mask & (mask >> dir)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    return (flip1 << dir) | (flip2 >> dir)


def move_gen(P, O):
    mask = O & 0x7E7E7E7E7E7E7E7E
    return ((move_gen_sub(P, mask, 1) \
             | move_gen_sub(P, O, 8) \
             | move_gen_sub(P, mask, 7) \
             | move_gen_sub(P, mask, 9)) & ~(P | O)) & FULL_MASK


def print_bitboard(BB):
    bitarr = [1 if (1 << i) & BB != 0 else 0 for i in range(64)]
    s = ""
    for rk in range(7, -1, -1):
        for fl in range(8):
            s += str(bitarr[fl + 8 * rk]) + " "
        s += "\n"
    print s


def to_bitboard(board):
    W = 0
    B = 0
    for r in range(8):
        for c in range(8):
            if board[c][r] == -1:
                B |= BIT[8 * r + c]
            elif board[c][r] == 1:
                W |= BIT[8 * r + c]
    return (W, B)


def to_move(bitmove):
    return (bitmove % 8, bitmove // 8)


def to_bitmove(move):
    return move[0] + 8 * move[1]


RADIAL_MAP = {}


def fill_radial_map():
    rad_map = {-1: (-1, 0), 1: (1, 0), -8: (0, -1), 8: (0, 1), -7: (1, -1), 7: (-1, 1), -9: (-1, -1), 9: (1, 1)}
    for dir, dirtup in rad_map.items():
        lis = [0] * 64
        for sqr in range(64):
            mask = 0
            sq = sqr
            x, y = to_move(sq)
            sq += dir
            x += dirtup[0]
            y += dirtup[1]
            while 0 <= x < 8 and 0 <= y < 8 and 0 <= sq < 64:
                mask |= BIT[sq]
                sq += dir
                x += dirtup[0]
                y += dirtup[1]
            lis[sqr] = mask
        RADIAL_MAP[dir] = lis


DIR = [
    [1, -7, -8],
    [-1, -9, -8],
    [1, 8, 9],
    [7, 8, -1],
    [8, 9, 1, -7, -8],
    [-1, 1, -7, -8, -9],
    [7, 8, -1, -9, -8],
    [7, 8, 9, -1, 1],
    [-1, 1, -7, 7, -8, 8, -9, 9]]

SQ_DIR = \
    [2, 2, 7, 7, 7, 7, 3, 3,
     2, 2, 7, 7, 7, 7, 3, 3,
     4, 4, 8, 8, 8, 8, 6, 6,
     4, 4, 8, 8, 8, 8, 6, 6,
     4, 4, 8, 8, 8, 8, 6, 6,
     4, 4, 8, 8, 8, 8, 6, 6,
     0, 0, 5, 5, 5, 5, 1, 1,
     0, 0, 5, 5, 5, 5, 1, 1]


def flip(W, B, mv):
    mask = 0
    for dir in DIR[SQ_DIR[mv]]:
        mvtmp = mv
        mvtmp += dir
        while mvtmp >= 0 and mvtmp < 64 and (BIT[mvtmp] & B != 0) and (BIT[mvtmp] & RADIAL_MAP[dir][mv] != 0):
            mvtmp += dir
        if (mvtmp >= 0 and mvtmp < 64 and BIT[mvtmp] & W != 0) and (BIT[mvtmp] & RADIAL_MAP[dir][mv] != 0):
            mvtmp -= dir
            while mvtmp != mv:
                mask |= BIT[mvtmp]
                mvtmp -= dir

    return mask


FULL_MASK = 0xFFFFFFFFFFFFFFFF
LSB_HASH = 0x07EDD5E59A4E28C2


def fill_lsb_table():
    bitmap = 1
    global LSB_TABLE
    LSB_TABLE = [0] * 64
    for i in range(64):
        LSB_TABLE[(((bitmap & (~bitmap + 1)) * LSB_HASH) & FULL_MASK) >> 58] = i
        bitmap <<= 1


def lsb(bitmap):
    return LSB_TABLE[(((bitmap & (~bitmap + 1)) * LSB_HASH) & FULL_MASK) >> 58]


def pop_lsb(bitmap):
    l = lsb(bitmap)
    bitmap &= bitmap - 1
    return l, bitmap & FULL_MASK


def count_bit(b):
    b -= (b >> 1) & 0x5555555555555555;
    b = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333));
    b = ((b >> 4) + b) & 0x0F0F0F0F0F0F0F0F;
    return ((b * 0x0101010101010101) & FULL_MASK) >> 56


def count_bit_2(b):
    raise DeprecationWarning
    cnt = 0
    for i in range(64):
        if b & BIT[i] != 0:
            cnt += 1
    return cnt


# helper: print a hex representation of the position
def pos2hex(*plist):
    n = 0
    for p in plist:
        n |= BIT[p]
    print_bitboard(n)
    s = hex(n).upper()
    return "0x" + s[2:]


engine = MctsEngine