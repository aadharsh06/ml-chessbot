
from os import environ as env
env['TF_CPP_MIN_LOG_LEVEL'] = '3'

import chess as ch
import numpy as np
import tensorflow as tf
import index_moves as im
import neural_net as nn
import socket
import threading

HOST = '127.0.0.1'
PORT = 65432

model = nn.cnn()
model.compile ( optimizer = 'adam',
    loss = {
        "policy" : tf.keras.losses.CategoricalCrossentropy ( from_logits = True ),
        "value" : tf.keras.losses.MeanSquaredError()
} )

def get_new_board ( data ):
    fen, move_index = data.split ( '$' )
    cur_player = fen.split()[1]
    board = ch.Board ( fen )
    board.push ( ch.Move.from_uci ( im.return_move ( int ( move_index ) ) ) )
    new_fen = board.fen()
    new_fen = new_fen.split() 
    new_fen[1] = cur_player
    return ' '.join ( new_fen )

def get_legal_moves ( fen ):
    board = ch.Board ( fen )
    legal_moves = [ str ( im.return_index ( move.uci() ) ) for move in board.legal_moves ]
    return ' '.join ( legal_moves )

def neural_net ( fen ):
    legal_moves = list ( map ( int, get_legal_moves ( fen ).split ( " " ) ) )
    x = nn.feature_planes ( fen )
    x = np.expand_dims ( x, axis = 0 )
    policy, value = model.predict ( x, verbose = 0 )

    policy = np.array ( policy[0][legal_moves] )
    exp_policy = np.exp ( policy )
    policy = exp_policy / np.sum ( exp_policy )
    
    policy = list ( map ( str, list ( policy ) ) )
    
    return ' '.join ( [ str ( value[0][0] ) ] + policy )

def client ( conn, addr ):
    with conn:
        while True:
            data = conn.recv ( 1024 )
            if not data:
                break
            req = data.decode().strip()
            
            function = req[0]
            data = req[1:]

            if ( function == '2' ):
                res = get_new_board ( data )
            elif ( function == '1' ):
                res = get_legal_moves ( data )
            elif ( function == '0'):
                res = neural_net ( data )

            conn.sendall ( res.encode() )

def start_server ( stop ):
    print ( "Server started\n" )
    with socket.socket ( socket.AF_INET, socket.SOCK_STREAM ) as s:
        s.bind ( ( HOST, PORT ) )
        s.listen()

        while not stop.is_set():
            conn, addr = s.accept()
            threading.Thread ( target = client, args = ( conn, addr ) ).start()
        s.close()