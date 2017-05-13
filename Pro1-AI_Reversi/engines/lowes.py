# -*- coding:utf-8 -*-  
from __future__ import absolute_import
from engines import Engine
from copy import deepcopy
from random import shuffle
import math

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
        self.root=None
        self.C=1.96
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

        if time_remaining < 3:
            self.depth = 5
        elif time_remaining < 0.8:
            self.depth = 4
        elif time_remaining < 0.5:
            self.depth = 3
        elif time_remaining < 0.3:
            self.depth = 2
        else:
            # 默认探索最大6层
            self.depth = 6
        
        return self.UCTSearch(self.root)

    def UCTSearch(self,state_node):
        # 节点已在之前创建
        while True:
            # 最深未被拓展的节点
            leafState=self.treePolicy(state_node,self.depth)
            
            # 模拟终局的结果 暂定1或0
            reward=self.defaultPolicy(leafState)
            # 回溯，更新祖先节点
            self.backup(leafState,reward)

            # 如果leafState已经是终局或深度超出阈值,则跳出循环
            if self.checkEnd(leafState['currState']) or self.depth<=1:
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
            print depth

   # 模拟直至终局,board请务必deepcopy之后再模拟   TODO 学长
    def defaultPolicy(self,state):
        board=deepcopy(state['currState'])
        currcolor=state['color']
        v=0
        while True: 
            legal_moves=board.get_legal_moves(currcolor)

            #判断终局
            if self.checkEnd(board):
                v=self.getFinalVal(board)
                break
            #随机招式
            else:
                # 非连下
                if len(legal_moves) != 0: 
                    # posVal=-999
                    # bestMv=None
                    # for mv in legal_moves:
                    #     if self.graph[mv[0]][mv[1]]>posVal:
                    #         posVal=self.graph[mv[0]][mv[1]]
                    #         bestMv=mv
                    # board.execute_move(bestMv, currcolor)
                    shuffle(legal_moves)
                    board.execute_move(legal_moves[0],currcolor)
                currcolor=-currcolor
        return v

    # 判断终局
    def checkEnd(self,board):
        # 自己的招式
        selfMoves=board.get_legal_moves(self.root['color'])
        # 对手的招式
        opponentMoves=board.get_legal_moves(-self.root['color'])
        # 判断终局
        if len(selfMoves)==0 and len(opponentMoves)==0:
            return True
        return False

    # 获得终局的reward
    def getFinalVal(self,board):
        v=0.5
        if self.count(board,self.root['color'])>self.count(board,-self.root['color']):
            v=1
        elif self.count(board,self.root['color'])<self.count(board,-self.root['color']):
            v=0
        return v

    def count(self,board,color):
        """ Count the number of pieces of the given color.
        (1 for white, -1 for black, 0 for empty spaces) """
        count = 0
        for y in range(8):
            for x in range(8):
                if board[x][y] == color:
                    count += 1
        return count

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
        targetEval=-999999
        color=state['color']
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
            if eval>targetEval:
                targetEval=eval
                targetMv=mv
                target_state=child
        return (targetMv,target_state)


engine=LowesEngine


