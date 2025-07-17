
import numpy as np
import chess.pgn as cg
import chess.engine as ce
import index_moves as im
from pickle import dump
from time import time
import os

overall_start = time()

pgn_pos = open ( r".\training_data\pos.txt", 'r' )
cur_pos = int ( pgn_pos.read() )
pgn_pos.close()

all_games = open ( r".\training_data\lichess_db_standard_rated_2013-01.pgn", 'r' )
all_games.seek ( cur_pos )

def get_engine_policy ( board ):
    anz = engine.analyse ( board, ce.Limit ( time = 1 ), multipv = min ( 10, len ( list ( board.legal_moves ) ) ) )

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
engine = ce.SimpleEngine.popen_uci ( ".\stockfish\stockfish-windows-x86-64-avx2.exe" )

total_games = 500

b = 1
while ( os.path.exists ( ".\training_data\b{}".format ( b ) ) ):
    b += 1
os.makedirs ("./training_data/b{}".format ( b ), exist_ok = True )

for g in range ( total_games ):
    start = time()

    moves = 0
    x = []
    
    game = cg.read_game ( all_games )
    cur_pos = all_games.tell()
    if game is None:
        break
    
    board = game.board()
    cur_fen = board.fen()

    for move in game.mainline_moves():
        considered_moves, p_hat = get_engine_policy ( board )
        considered_moves = [ im.return_index ( i ) for i in considered_moves ]
        full_phat = im.empty_mv()
        full_phat[considered_moves] = p_hat
        x.append ( [ cur_fen, list ( full_phat ), 0 ] )
        move = board.push ( move )
        moves += 1
        cur_fen = board.fen()
        #print ( "\nGame number: {}, Moves complete: {}\n".format ( g + 1, moves ), board, "\n", sep = "" )
        
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

    with open ( "./training_data/b{}/x{}.pkl".format ( b, g ), 'wb' ) as f:
        dump ( x, f )

    end = time()

    print ( "\Game {} Complete: {} minutes".format ( g+1, (end - start)/60 ) )

    pgn_pos = open ( r".\training_data\pos.txt", 'w' )
    pgn_pos.write ( str ( cur_pos ) )
    pgn_pos.close()

engine.quit()
print ( "\nProgram Complete: Total time --> {} hours".format ( ( time() - overall_start ) / 3600 ) )