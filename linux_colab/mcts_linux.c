
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#define CH_MAX 120
#define TREE_SIZE 10000
#define SIM_MAX 800
#define Cpuct 1.414

struct Node {
    char state[100];
    double node_val;
    int n_actions;
    int N[CH_MAX];
    double W[CH_MAX];
    double P[CH_MAX];
    int a[CH_MAX];
    struct Node *children[CH_MAX];
    int n_children;
    bool ch_exist;
};

static void *all_pointers[TREE_SIZE];
static int p = 0;
static int sockfd;

void init_server_conn() {
    struct sockaddr_in server_addr;

    sockfd = socket ( AF_INET, SOCK_STREAM, 0 );

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons ( 65432 );
    server_addr.sin_addr.s_addr = inet_addr ( "127.0.0.1" );

    connect ( sockfd, ( struct sockaddr* )&server_addr, sizeof ( server_addr ) );
}

char *server_call ( const char *push ) {
    char *data = calloc ( 1024, sizeof ( char ) );

    ssize_t sent = send ( sockfd, push, strlen ( push ), 0 );
    ssize_t recv_size = recv ( sockfd, data, 1024 - 1, 0 );
    data[recv_size] = '\0';

    all_pointers[p++] = data;
    return data;
}

void close_server_conn() {
    close ( sockfd );
}

void set_zeros_double ( double *arr, int size ) {
    for ( int i = 0; i < size; i++ ) {
        arr[i] = 0.0;
    }
}
void set_zeros_int ( int *arr, int size ) {
    for ( int i = 0; i < size; i++ ) {
        arr[i] = 0;
    }
}

double *neural_net ( char stat[100] ) {
    char state[120];
    strcpy ( state + 1, stat );
    state[0] = '0';
    state[strlen ( stat ) + 1] = '\0';

    char *st = server_call ( state );
    double *nn = calloc ( 100, sizeof ( double ) );
    all_pointers[p++] = nn;

    int i = 0;
    char *token = strtok ( st, " " );
    while ( token != NULL ) {
        nn[i++] = atof ( token );
        token = strtok ( NULL, " " );
    }
    return nn;
}

int *get_legal_moves ( char stat[100], int *size ) {
    char state[120];
    strcpy ( state + 1, stat );
    state[0] = '1';
    state[strlen ( stat ) + 1 ] = '\0';

    char *st = server_call ( state );
    int *legal = calloc ( CH_MAX, sizeof ( int ) );
    all_pointers[p++] = legal;

    int i = 0;
    char *token = strtok ( st, " " );
    while ( token != NULL ) {
        legal[i++] = atoi ( token );
        token = strtok ( NULL, " " );
    }
    *size = i;
    return legal;
}

char *get_new_board ( const char stat[100], int move_index ) {
    char state[120];
    int len = strlen ( stat );
    strcpy ( state + 1, stat );
    state[0] = '2';
    state[len+1] = '$';
    sprintf ( state + len + 2, "%d", move_index );
    return server_call ( state );
}

struct Node *init_node ( char *board )
{
    struct Node *node = malloc ( sizeof ( struct Node ) );
    int *legal_moves;
    int n_moves;
    double *nn;

    memcpy ( node->state, board, 100 * sizeof ( char ) );
    
    legal_moves = get_legal_moves ( board, &n_moves );
    memcpy ( node->a, legal_moves, n_moves * sizeof ( legal_moves[0] ) );

    nn = neural_net ( board );
    node->node_val = nn[0];
    node->n_actions = n_moves;
    
    set_zeros_int ( node->N, n_moves );
    set_zeros_double ( node->W, n_moves );
    memcpy ( node->P, nn + 1, n_moves * sizeof ( double ) );

    for ( int i = 0; i < CH_MAX; i++ ) {
        node->children[i] = NULL;
    }
    node->n_children = 0;
    node->ch_exist = false;

    all_pointers[p++] = node;
    return node;
}

double *return_pi ( char given_board[100], int given_moves  )
{
    init_server_conn();
    p = 0;
    struct Node *root = init_node ( given_board );  

    for ( int i = 0; i < SIM_MAX; i++ ) {
        struct Node *cur_node = root;
        struct Node *history_node[TREE_SIZE];
        int history_action[TREE_SIZE];
        int k = 0;
        while ( 1 ) {
            history_node[k] = cur_node;
            int a_star = 0;
            double a_star_val = 0;

            double sigma_b = 0;
            for ( int t = 0; t < cur_node->n_actions; t++ ) {
                sigma_b += cur_node->N[t];
            }

            for ( int j = 0; j < cur_node->n_actions; j++ ) {
                double qsa = 0, usa = 0, total = 0;
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
                break;
            }
            history_action[k] = a_star;
            k += 1;
        }
        double val = cur_node->node_val;
        for ( int j = k - 1; j >= 0; j-- ) {
            history_node[j]->N[history_action[j]] += 1;
            history_node[j]->W[history_action[j]] += val;
        }
    }
    double tau;
    if ( given_moves < 10 ) {
        tau = 0.9;
    }
    else if ( given_moves < 20 ) {
        tau = 0.5;
    }
    else {
        tau = 0.2;
    }
    double sigma_b_tau = 0;
    for ( int j = 0; j < root->n_actions; j++ ) {
        sigma_b_tau += pow ( root->N[j], tau );
    }
    
    double *pi = calloc ( root->n_actions, sizeof ( double ) );
    for ( int j = 0; j < root->n_actions; j++ ) {
        pi[j] = pow ( root->N[j], tau ) / sigma_b_tau;
    }
    close_server_conn();
    return pi;
}
