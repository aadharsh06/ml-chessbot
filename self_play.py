
import numpy as np
import chess as ch
import index_moves as im
import threading
import py_server
import socket
from ctypes import CDLL, POINTER, c_int, c_char_p, c_double

HOST = "127.0.0.1"
PORT = 65432

t = threading.Thread ( target = py_server.start_server )
t.start()

lib = CDLL ( "./mcts.dll" )

pi = lib.return_pi
pi.argtypes = [ c_char_p, c_int ]
pi.restype  = POINTER ( c_double )

board = ch.Board()
cur_fen = board.fen()
moves = 0

while ( not board.is_checkmate() ):
    legal_moves = [ str ( im.return_index ( move.uci() ) ) for move in ch.Board ( cur_fen ).legal_moves ]
    p_hat = pi ( cur_fen.encode(), moves )
    p_hat = [ p_hat[i] for i in range ( len ( legal_moves ) ) ]
    move = board.push_uci ( im.return_move ( int ( np.random.choice ( legal_moves, p = p_hat ) ) ) )
    cur_fen = board.fen()
    moves += 1
    print ( "\nMoves complete: {}\n".format ( moves ), board, "\n" )

with socket.socket ( socket.AF_INET, socket.SOCK_STREAM ) as s:
    s.connect ( (HOST, PORT ) )
    s.sendall ( b"30" )
    s.close()
