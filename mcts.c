
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <string.h>

#define CH_MAX 120
#define TREE_SIZE 10000
#define SIM_MAX 800
#define Cpuct 1.414

struct Node {
    char state[8][8];
    float node_val;
    int n_actions;
    int N[CH_MAX];
    float W[CH_MAX];
    float P[CH_MAX];
    int a[CH_MAX];
    struct Node *children[CH_MAX];
    int n_children;
    bool ch_exist;
};

void *all_pointers[TREE_SIZE];
int p = 0;

float *neural_net ( char state[8][8], int n_moves )
{
    return 0;
}
int *get_legal_moves ( char state[8][8], int *size )
{
    return 0;
}
char *get_new_board ( char state[8][8], int move_index )
{
    return 0;
}
void set_zeros ( int *arr, int size )
{
    for ( int i = 0; i < size; i++ ) {
        *(arr+i) = 0;
    }
}

struct Node *init_node ( char *board )
{
    struct Node *node = malloc ( sizeof ( struct Node ) );
    int *legal_moves;
    int n_moves;
    float *nn;
    
    legal_moves = get_legal_moves ( board, &n_moves );
    memcpy ( node->a, legal_moves, n_moves * sizeof ( legal_moves[0] ) );

    memcpy ( node->state, board, 8 * 8 * sizeof ( char ) );
    nn = neural_net ( board, n_moves );
    node->node_val = nn[0];
    node->n_actions = n_moves;
    
    set_zeros ( node->N, n_moves );
    set_zeros ( node->W, n_moves );
    memcpy ( node->P, nn + 1, n_moves * sizeof ( float ) );

    for ( int i = 0; i < CH_MAX; i++ ) {
        node->children[i] = NULL;
    }
    node->n_children = 0;
    node->ch_exist = false;

    all_pointers[p++] = node;
    return node;
}

float *return_pi ( char given_board[8][8], int given_moves )
{
    // How many moves have been played in the game till then : given_moves
    p = 0;
    struct Node *root = init_node ( given_board );

    for ( int i = 0; i < SIM_MAX; i++ ) {
        struct Node *cur_node = root;
        struct Node *history_node[TREE_SIZE];
        int history_action[TREE_SIZE];
        int k = 0;
        while ( cur_node->ch_exist == true ) {

            history_node[k] = cur_node;
            int a_star = 0;
            float a_star_val = 0;

            double sigma_b = 0;
            for ( int t = 0; t < cur_node->n_actions; t++ ) {
                sigma_b += cur_node->N[t];
            }

            for ( int j = 0; j < cur_node->n_actions; j++ ) {
                float qsa = 0, usa = 0, total = 0;
                if ( cur_node->N[j] != 0 ) {
                    qsa = cur_node->W[j] / cur_node->N[j];
                }
                usa = Cpuct * cur_node->P[j] * ( ( sqrt ( sigma_b ) ) / ( 1  + cur_node->N[j] ) );
                total = qsa + usa;
                if ( total > a_star_val ) {
                    a_star = j;
                    a_star_val = total;
                }
            }
            if ( cur_node->children[a_star] ) {
                cur_node = cur_node->children[a_star];
            }
            else {
                struct Node *child_node = malloc ( sizeof ( struct Node ) );
                child_node = init_node ( get_new_board ( cur_node->state, cur_node->a[a_star] ) );
                cur_node->children[a_star] = child_node;
                cur_node->n_children += 1;
                cur_node->ch_exist = true;
                cur_node = child_node;
                all_pointers[p++] = child_node;
            }
            history_action[k] = a_star;
            k += 1;
        }
        float val = cur_node->node_val;
        for ( int j = k - 1; j >= 0; j-- ) {
            history_node[j]->N[history_action[j]] += 1;
            history_node[j]->W[history_action[j]] += val;
        }
    }

    float tau;
    if ( given_moves < 10 ) {
        tau = 0.9;
    }
    else if ( given_moves < 20 ) {
        tau = 0.5;
    }
    else {
        tau = 0.2;
    }
    float sigma_b_tau = 0;
    for ( int j = 0; j < root->n_actions; j++ ) {
        sigma_b_tau += pow ( root->N[j], tau );
    }

    float *pi = calloc ( root->n_actions, sizeof ( float ) );
    for ( int j = 0; j < root->n_actions; j++ ) {
        pi[j] = pow ( root->N[j], tau ) / sigma_b_tau;
    }

    for ( int i = 0; i < p; i++ ) {
        free ( all_pointers[i] );
    }

    return pi;
}