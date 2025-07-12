
import numpy as np
import chess as ch
import index_moves as im
from re import split as re_split

def board_np ( board ):
    return np.array ( re_split ( r'[ \n]+', str ( board ) ) ).reshape ( 8, 8 )

