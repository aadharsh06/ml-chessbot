
import numpy as np
import chess as ch
import chess.engine as ce
import index_moves as im
import threading
import py_server
from pickle import dump
from time import time

from ctypes import CDLL, POINTER, c_int, c_char_p, c_double

start = time()

engine = ce.SimpleEngine.popen_uci(r".\stockfish\stockfish-windows-x86-64-avx2.exe")

engine.configure ( {
    "UCI_LimitStrength": True,
    "UCI_Elo": 1800
} )

def get_engine_policy ( board ):
    anz = engine.analyse( board, ce.Limit ( time = 0.1 ), multipv = len ( [ str ( im.return_index ( move.uci() ) ) for move in board.legal_moves ] ) )

    moves = []
    scores = []
    for i in anz:
        mv = i["pv"][0]
        sc = i["score"].white().score()
        moves.append ( mv.uci() )
        scores.append ( sc )

    scores = np.array ( scores, dtype = np.float64 )
    scores = scores - scores.min()
    
    if scores.sum() > 0:
        policy = scores / scores.sum()
    else:
        policy = np.ones_like ( scores ) / len ( scores )

    return moves, policy


HOST = "127.0.0.1"
PORT = 65432

stop = threading.Event()
t = threading.Thread ( target = py_server.start_server, args = ( stop, ) )
t.start()

lib = CDLL ( "./mcts.dll" )

pi = lib.return_pi
pi.argtypes = [ c_char_p, c_int ]
pi.restype  = POINTER ( c_double )

board = ch.Board()
cur_fen = board.fen()
moves = 0

x = []

while ( not board.is_game_over() ):
    # Engine plays frst
    legal_moves, p_hat = get_engine_policy ( board )
    legal_moves = [ im.return_index ( i ) for i in legal_moves ]
    full_phat = im.empty_mv()
    full_phat[legal_moves] = p_hat
    x.append ( ( cur_fen, list ( full_phat ), 0 ) )
    move = board.push_uci ( im.return_move ( int ( np.random.choice ( legal_moves, p = p_hat ) ) ) )
    moves += 1
    cur_fen = board.fen()
    print ( "\nMoves complete: {}\n".format ( moves ), board, "\n", sep = "" )
    
    if ( board.is_game_over() ):
        break
    
    # NN plays second
    legal_moves = [ im.return_index ( move.uci() ) for move in ch.Board ( cur_fen ).legal_moves ]
    p_hat = pi ( cur_fen.encode(), moves )
    p_hat = [ p_hat[i] for i in range ( len ( legal_moves ) ) ]
    full_phat = im.empty_mv()
    full_phat[legal_moves] = p_hat
    x.append ( ( cur_fen, list ( full_phat ), 0 ) )
    move = board.push_uci ( im.return_move ( int ( np.random.choice ( legal_moves, p = p_hat ) ) ) )
    cur_fen = board.fen()
    moves += 1
    print ( "\nMoves complete: {}\n".format ( moves ), board, "\n", sep = "" )
    
print ( "\Game over" )

if board.result() == "1-0":
    white = 1
elif board.result() == "0-1":
    white = -1
else:
    white = 0

for i in range ( len ( x ) ):
    if i % 2 == 0:
        x[i][2] = white
    else:
        x[i][2] = (-1) * white

with open ( "./training_data/x.pkl", 'wb' ) as f:
    dump ( x, f )

stop.set()
engine.quit()

end = time()

print ( "\nProgram Complete: {} minutes".format ( (end - start)/60 ) )