# -*- coding:utf-8 -*-  
from __future__ import absolute_import
from engines import Engine
from copy import deepcopy
from random import shuffle
import math
import timeit

class LowesEngine(Engine):
    def __init__(self):
        # state_node
        # {
        #    parentState: old_state_node
        #    currState: board    
        #    childState:{
        #        move:state_node
        #      }
        #    color:-1 1
        #    count:  访问了几次该节点
        #    eval: 胜利率，为所有者子节点胜利率的平均值。终局的胜利率为1或-1
        # }
        fill_bit_table()
        fill_radial_map()
        self.root=None
        self.C=1.96
        self.time=0
        # 棋盘各点权值图
        self.graph=[
            [99,-8,8,6,6,8,-8,99],
            [-8,-24,-4,-3,-3,-4,-24,-8],
            [8,-4,7,4,4,7,-4,8],
            [6,-3,4,0,0,4,-3,6],
            [6,-3,4,0,0,4,-3,6],
            [8,-4,7,4,4,7,-4,8],
            [-8,-24,-4,-3,-3,-4,-24,-8],
            [99,-8,8,6,6,8,-8,99]
        ]
    
    # def display(self,board,time):
    #     """" Display the board and the statistics of the ongoing game. """
    #     print "    A B C D E F G H"
    #     print "    ---------------"
    #     for y in range(7,-1,-1):
    #         # Print the row number
    #         print str(y+1) + ' |',
    #         for x in range(8):
    #             # Get the piece to print
    #             piece = board[x][y]
    #             if piece == -1:
    #                 print "B",
    #             elif piece == 1:
    #                 print "W",
    #             else:
    #                 print ".",
    #         print '| ' + str(y+1)

    #     print "    ---------------"
    #     print "    A B C D E F G H\n"

    #     print "STATISTICS (score / remaining time):"
    #     print "Black: " + str(self.count(-1)) + ' / ' + str(time[-1])
    #     print "White: " + str(self.count(1)) + ' / ' + str(time[1]) + '\n'
        

    def get_move(self,board,color,move_num=None,time_remaining=None,time_opponent=None):        
        self.root={}
        self.root['parentState']=None
        self.root['currState']=board
        self.root['childState']={}
        self.root['color']=color
        self.root['count']=1
        self.root['eval']=0

        if time_remaining < 1000:
            self.depth = 7
        elif time_remaining < 500:
            self.depth = 6
        elif time_remaining < 200:
            self.depth = 5
        elif time_remaining < 100:
            self.depth = 4
        elif time_remaining < 50 :
            self.depth = 3
        elif time_remaining < 20:
            self.depth = 2
        else:
            # 默认探索最大8层
            self.depth = 8
        
        return self.UCTSearch(self.root)

    def UCTSearch(self,state_node):
        time_begin=timeit.default_timer()
        # 节点已在之前创建
        while True:
            # 最深未被拓展的节点
            leafState=self.treePolicy(state_node,self.depth)
            
            # 模拟终局的结果 暂定1或0
            reward=self.defaultPolicy(leafState)
            # 回溯，更新祖先节点
            self.backup(leafState,reward)

            # 如果leafState已经是终局或深度超出阈值或即将超时,则跳出循环
            if self.checkEnd(leafState['currState']) or self.depth<=1 \
            or round(timeit.default_timer()-time_begin,1)>=56:
                break

        return self.bestChild(state_node,self.C)[0]

    # 选举出最深的未被完全拓展的节点  TODO 思昊
    def treePolicy(self,state,depth):       
        while True:
            board=state['currState']
            legal_moves=board.get_legal_moves(state['color'])
            # 判断是否对手连下的点
            if len(legal_moves) == 0:
                return state
            
            childKeys=state['childState'].keys()
            for mv in legal_moves:
                # 如果没有拓展该招式
                if mv not in childKeys:
                    return self.expand(mv, state)

            # 如果深度超出预定阈值
            if depth<=1:
                self.depth=depth
                return self.bestChild(state,self.C)[1]

            state=self.bestChild(state,self.C)[1]
            depth-=1

   # 模拟直至终局,board请务必deepcopy之后再模拟   TODO 学长
    def defaultPolicy(self,state):
        board=state['currState']
        currcolor=state['color']
        v=0
        mvlist = []
        W,B = to_bitboard(board)
        # 判断自己是黑还是白
        if currcolor == 1:
            selfTurn=W
            opponent=B
        else:
            selfTurn=B
            opponent=W
        while True:
            legal_moves=gen_movelist(selfTurn,opponent)
            if len(legal_moves) == 0 and len(gen_movelist(opponent,selfTurn)) == 0:
                v = self.getFinalVal(selfTurn,opponent,currcolor)
                break
            else:
                if len(legal_moves) != 0:                
                    shuffle(legal_moves)
                    # 参照位置权重来选择模拟的棋步
                    posVal=-999
                    bestMv=None
                    for mv in legal_moves:
                        tmv=to_move(mv)
                        if self.graph[tmv[0]][tmv[1]]>posVal:
                            posVal=self.graph[tmv[0]][tmv[1]]
                            bestMv=mv
                    # 翻转                   
                    flipmask = flip(selfTurn,opponent,bestMv)
                    selfTurn ^= flipmask | BIT[bestMv]
                    opponent ^= flipmask
                # 换手
                t=selfTurn
                selfTurn=opponent
                opponent=t
                currcolor=-currcolor
        return v

    # 判断终局
    def checkEnd(self,board):
        W,B=to_bitboard(board)
        if self.root['color'] == -1:
            selfTurn=B
            opponent=W
        else:
            selfTurn=W
            opponent=B
        # 自己的招式
        selfMoves=move_gen(selfTurn,opponent)
        # 对手的招式
        opponentMoves=move_gen(opponent,selfTurn)
        # 判断终局
        if selfMoves==0 and opponentMoves==0:
            return True
        return False

    # 获得终局的reward
    def getFinalVal(self,P,O,color):
        v=0.5
        if count_bit(P)>count_bit(O):
            if color == self.root['color']:
                v=1
            else:
                v=0
        elif count_bit(P)<count_bit(O):
            if color == self.root['color']:
                v=0
            else:
                v=1
        return v

    # 回溯
    def backup(self,state,reward):
        while state:
            state['eval']=(state['eval']*state['count']+reward)/float(state['count']+1)
            state['count']+=1
            state=state['parentState']
        return

    # 扩展节点  TODO 思昊
    def expand(self, mv, state_node):  
        # 初始化新节点
        state={}
        state['parentState'] = state_node
        state['currState'] = deepcopy(state_node['currState'])
        state['childState'] = {}
        state['count'] = 1
        state['eval'] = 0
        
        # 执行mv操作
        state['currState'].execute_move(mv, state_node['color'])
        
        # 判断新节点颜色
        legal_moves=state['currState'].get_legal_moves(-state_node['color'])
        if len(legal_moves) == 0:
            state['color'] = state_node['color']
        else:
            state['color'] = -state_node['color']
        
        # 添加进入子节点
        state_node['childState'][mv] = state
        return state

    # 返回招式与子节点的元组 区分对手节点和自身节点
    def bestChild(self,state,C):
        targetMv=None
        color=state['color']
        if color==self.root['color']:
            targetEval=-999999
        else:
            targetEval=999999
        target_state=None
        childList=state['childState']
        for mv in childList:
            child=childList[mv]
            # # 优先占角
            # if (mv[0]==0 or mv[0]==7) and (mv[1]==0 and mv[1]==7):
            #     return (mv,child)
            # # 次优先占边
            # if mv[0]==0 or mv[0]==7 or mv[1]==0 or mv[1]==7:
            #     return (mv,child)
            # UCB
            eval=child['eval']+math.sqrt(C*math.log(state['count'])/float(child['count']))
            if color == self.root['color']:
                if eval>targetEval:
                    targetEval=eval
                    targetMv=mv
                    target_state=child
            else:
                if eval<targetEval:
                    targetEval=eval
                    targetMv=mv
                    target_state=child
        return (targetMv,target_state)

DIR = [
[1, -7, -8],
[-1,-9,-8],
[1,8,9],
[7,8,-1],
[8,9,1,-7,-8],
[-1,1,-7,-8,-9],
[7,8,-1,-9,-8],
[7,8,9,-1,1],
[-1, 1, -7,7,-8,8,-9,9]]

SQ_DIR = \
[2, 2, 7, 7, 7, 7, 3, 3,
 2, 2, 7, 7, 7, 7, 3, 3,
 4, 4, 8, 8, 8, 8, 6, 6,
 4, 4, 8, 8, 8, 8, 6, 6,
 4, 4, 8, 8, 8, 8, 6, 6,
 4, 4, 8, 8, 8, 8, 6, 6,
 0, 0, 5, 5, 5, 5, 1, 1,
 0, 0, 5, 5, 5, 5, 1, 1 ]

FULL_MASK = 0xFFFFFFFFFFFFFFFF
# 执行棋步
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

RADIAL_MAP = {}

def fill_radial_map():
    rad_map = {-1: (-1, 0), 1:(1, 0), -8:(0, -1), 8:(0, 1), -7:(1, -1), 7:(-1, 1), -9:(-1, -1), 9:(1, 1)}
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

# 将点阵的move转化为坐标
def to_move(bitmove):
    return (bitmove % 8, bitmove / 8)

# 将坐标转化为点阵的move
def to_bitmove(move):
    return move[0] + 8 * move[1]

def move_gen_sub(P, mask, dir):
    dir2 = long(dir * 2)
    flip1  = mask & (P << dir)
    flip2  = mask & (P >> dir)
    flip1 |= mask & (flip1 << dir)
    flip2 |= mask & (flip2 >> dir)
    mask1  = mask & (mask << dir)
    mask2  = mask & (mask >> dir)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    return (flip1 << dir) | (flip2 >> dir)

# 寻找合法棋步
def move_gen(P, O):
    mask = O & 0x7E7E7E7E7E7E7E7E
    return ((move_gen_sub(P, mask, 1) \
            | move_gen_sub(P, O, 8)  \
            | move_gen_sub(P, mask, 7) \
            | move_gen_sub(P, mask, 9)) & ~(P|O)) & FULL_MASK
# 创建棋步
def fill_bit_table():
    global BIT
    BIT = [1 << n for n in range(64)]

# 计算分数
def count_bit(b):
    b -=  (b >> 1) & 0x5555555555555555
    b  = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333))
    b  = ((b >> 4) + b)  & 0x0F0F0F0F0F0F0F0F
    return ((b * 0x0101010101010101) & FULL_MASK) >> 56

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

def fill_bit_table():
    global BIT
    BIT = [1 << n for n in range(64)]


def gen_movelist(W,B):
    mvlist=[]
    legal_moves=move_gen(W,B)
    if legal_moves != 0:
        for n in xrange(0,63):
            if legal_moves & BIT[n] != 0:
                mvlist.append(n)
    return mvlist



engine=LowesEngine


