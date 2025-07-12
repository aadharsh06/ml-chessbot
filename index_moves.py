
"""
Purpose: Handle all functions related to the indexing of moves.
"""

import numpy as np
import chess

letters = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h' ]
numbers = [ '1', '2', '3', '4', '5', '6', '7', '8' ][::-1]
prom = [ 'q', 'r', 'k', 'b' ]

# Considering all normal moves 64 * 64

c = [ i + j for i in letters for j in numbers ]
moves = [ i + j for i in c for j in c ]

# Handling promotions

board = np.array ( c ).reshape ( 8, 8 ).T
white_prom = [ i + j + k for j in board[0] for i in board[1] for k in prom ]
black_prom = [ i + j + k for j in board[6] for i in board[7] for k in prom ]

# Total moves

moves = moves + white_prom + black_prom + [ None ]

# Functions for external use

def mk_mvdict():
    """Return am empty move dictionary"""
    return dict ( zip ( moves, list ( np.zeros ( len ( moves ) ) ) ) )

def return_index ( move ):
    """Return index of a given move"""
    return moves.index ( move )

def conv_mv ( board, move ):
    # Convert a move from the chess module encoding to our encoding
    pass
