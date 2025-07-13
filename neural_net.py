
import numpy as np
import chess as ch
import tensorflow as tf
from tensorflow.keras import layers, Model, Input
from re import split as re_split

def feature_planes ( fen ):
    b = np.array ( re_split ( r'[ \n]+', str ( ch.Board ( fen ) ) ) ).reshape ( 8, 8 )
    fen_split = fen.split ( " " )[::-1]
    castling_rights = fen_split[2]
    to_move = fen_split[3]
    
    fp1 = np.where ( b == 'p', 1, 0 )
    fp2 = np.where ( b == 'q', 1, 0 )
    fp3 = np.where ( b == 'r', 1, 0 )
    fp4 = np.where ( b == 'b', 1, 0 )
    fp5 = np.where ( b == 'k', 1, 0 )
    fp6 = np.where ( b == 'n', 1, 0 )
    fp7 = np.where ( b == 'P', 1, 0 )
    fp8 = np.where ( b == 'Q', 1, 0 )
    fp9 = np.where ( b == 'R', 1, 0 )
    fp10 = np.where ( b == 'B', 1, 0 )
    fp11 = np.where ( b == 'K', 1, 0 )
    fp12 = np.where ( b == 'N', 1, 0 )
    fp13 = np.ones ( ( 8, 8 ), dtype = int ) if ( 'k' in castling_rights ) else np.zeros ( ( 8, 8 ), dtype = int )
    fp14 = np.ones ( ( 8, 8 ), dtype = int ) if ( 'q' in castling_rights ) else np.zeros ( ( 8, 8 ), dtype = int )
    fp15 = np.ones ( ( 8, 8 ), dtype = int ) if ( 'K' in castling_rights ) else np.zeros ( ( 8, 8 ), dtype = int )
    fp16 = np.ones ( ( 8, 8 ), dtype = int ) if ( 'Q' in castling_rights ) else np.zeros ( ( 8, 8 ), dtype = int )
    fp17 = np.ones ( ( 8, 8 ), dtype = int ) if ( to_move == 'w' ) else np.zeros ( ( 8, 8 ), dtype = int )
    
    return np.array ( [ fp1, fp2, fp3, fp4, fp5, fp6, fp7, fp8, fp9, fp10, fp11, fp12, fp13, fp14, fp15, fp16, fp17 ] ).T
    

def residual_block ( x_in ):
    x = layers.Conv2D ( 256, ( 3, 3 ), padding = 'same' )( x_in )
    x = layers.BatchNormalization()( x )
    x = layers.ReLU()( x )
    
    x = layers.Conv2D ( 256, ( 3, 3 ), padding = 'same' )( x )
    x = layers.BatchNormalization()( x )
    
    x = layers.Add()( [ x_in, x ] )
    x = layers.ReLU()( x )
    return x

def cnn():
    inputs = Input ( shape = ( 8, 8, 17 ) )
    
    x = layers.Conv2D ( 256, (3, 3), padding = 'same' )( inputs )
    x = layers.BatchNormalization()( x )
    x = layers.ReLU()( x )
    
    for _ in range ( 5 ):
        x = residual_block ( x )

    p = layers.Conv2D ( 2, ( 1, 1 ), padding = 'same' )( x )
    p = layers.BatchNormalization()( p )
    p = layers.ReLU()( p )
    p = layers.Flatten() ( p )
    p = layers.Dense ( 4672, name = "policy" ) ( p )

    v = layers.Conv2D ( 1, ( 1, 1 ), padding = 'same' )( x )
    v = layers.BatchNormalization()( v )
    v = layers.ReLU()( v )
    v = layers.Flatten()( v )
    v = layers.Dense( 256 )( v )
    v = layers.ReLU()( v )
    v = layers.Dense ( 1, activation = 'tanh', name = "value" )( v )

    model = Model ( inputs = inputs, outputs = [ p, v ] )
    return model