import numpy as numpy
from Lowes_restore import readImg,computeError

# example
computeError(readImg('D_recoverLinear.png'),readImg('D.png'),'D')
computeError(readImg('E_recoverLinear.png'),readImg('E.png'),'E')
computeError(readImg('F_recoverLinear.png'),readImg('F.png'),'F')