
import time
import os
import chess as ch
import numpy as np
import tensorflow as tf
import index_moves as im
import neural_net as nn

model = nn.cnn()
model.compile ( optimizer = 'adam',
    loss = {
        "policy" : tf.keras.losses.CategoricalCrossentropy ( from_logits = True ),
        "value" : tf.keras.losses.MeanSquaredError()
} )

def get_new_board ( data ):
    fen, move_index = data.split ( '$' )
    board = ch.Board ( fen )
    board.push ( ch.Move.from_uci ( im.return_move ( int ( move_index ) ) ) )
    return board.fen()

def get_legal_moves ( fen ):
    board = ch.Board ( fen )
    legal_moves = [ str ( im.return_index ( move.uci() ) ) for move in board.legal_moves ]
    return ' '.join ( legal_moves )

def neural_net ( fen ):
    legal_moves = get_legal_moves ( fen )
    x = nn.feature_planes ( fen )
    policy, value = model.predict ( x )
    
    policy = np.array ( policy[legal_moves] )
    exp_policy = np.exp ( policy )
    policy = exp_policy / np.sum ( exp_policy )
    
    return ' '.join ( [ value ] + policy )

while True:
    if os.path.exists ( "request.txt" ):
        with open ( "request.txt", "r" ) as f:
            req = f.read().strip()
            function = req[0]
            data = req[1:]
        os.remove ( "request.txt" )
        
        res = ""
        if ( function == '2' ):
            res = get_new_board ( data )
        elif ( function == '1' ):
            res = get_legal_moves ( data )
        elif ( function == '0'):
            res = neural_net ( data )
        
        with open ( "response.tmp", "w" ) as f:
            f.write ( res )
        os.rename ( "response.tmp", "response.txt" )
    else:
        time.sleep ( 0.001 )

