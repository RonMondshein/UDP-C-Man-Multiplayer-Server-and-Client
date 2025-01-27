import socket
import sys
import shared_libary as sl
import cman_utils as cu
import time
import copy
from cman_game import Player


BUFFERSIZE = 1024
FUNCTIONS = {
    # Client messages
    sl.OPCODE.GAME_STATE_UPDATE: sl.unpack_game_state_update_server,
    sl.OPCODE.GAME_END: sl.unpack_game_end_server,
    sl.OPCODE.ERROR: sl.unpack_error_server
}


def connect_to_server(client_socket, host, port, role):
    """
    Send a join message to the server with the selected role.

    Parameters:
    client_socket (socket): The client socket.
    host (str): Server address.
    port (int): Server port.
    role (str): Player role (cman, spirit, or watcher).
    """
    print(f"Connecting to server at {host}:{port} as {role}...")
    join_message = sl.pack_join_User(role)
    client_socket.sendto(join_message, (host, port))


def listen_to_server_non_blocking(client_socket):
    """
    Non-blocking function to listen for messages from the server and handle them.

    Parameters:
    client_socket (socket): The client socket.
    """
    try:
        message, sender_address = client_socket.recvfrom(BUFFERSIZE)
        opcode = message[0]
        
        handler = FUNCTIONS.get(opcode, None) #get the handler function for the opcode

        if handler:
            data = handler(message[1:]) #call the handler function with the data

            if opcode == sl.OPCODE.GAME_STATE_UPDATE: 
                print_board(data)

            elif opcode == sl.OPCODE.GAME_END:
                cu.clear_print("Game Over, winner", "CMAN" if data['winner'] == Player.CMAN else "SPIRIT" )
                return False  # Stop the game loop

            elif opcode == sl.OPCODE.ERROR:
                cu.clear_print("Error:", data)
                return False  # Stop the game loop
        else:
            cu.clear_print("Unknown message received from server.")
    except BlockingIOError:
        # No message received; continue
        pass
    except Exception as e:
        cu.clear_print("Error while listening to server:", e)
        return False  # Stop the game loop
    return True


def setup_board_from_file():
    """
    Setup the game board from the map.txt file.
    Returns:
    list: The initial game board state.
    list: The indices of the collectible points.
    """
    point_indices = []
    with open('map.txt', 'r') as file:
        init_board = [list(line.strip()) for line in file] 
    for i in range(len(init_board)):
        for j in range(len(init_board[i])):
            if init_board[i][j] == 'P': # if Point, add to point_indices
                point_indices.append((i,j))
            if init_board[i][j] != 'W': # if not Wall, change to empty (visoualization propuse)
                init_board[i][j] = ' '
    return init_board, sorted(point_indices) #return board and point_indices sorted (for predictability, consistency, and efficiency use)

def print_board(data):
    """
    Print the game board based on the received data from the server.
    Parameters:
    data (dict): The data received from the server.
    """

    cman_position = data['c_coords'] #get the cman position from the data dictionary
    spirit_position = data['s_coords']  #get the spirit position from the data dictionary
    points_status = (data['collected']) #get the points status from the data dictionary
    attempts = data['attempts'] #get the attempts from the data dictionary
    left_points = 0 
    default_board_state, collectible_points = setup_board_from_file() #get the default board state and the collectible points
    board = copy.deepcopy(default_board_state) #copy the default board state to the board
    for i in range(len(collectible_points)): 
        if not points_status[i]: #change_collected
            left_points += 1
            board[collectible_points[i][0]][collectible_points[i][1]] = 'P' #change the point to P (visual propuse)
    cu.clear_print()
    if 255 == cman_position[0] == cman_position[1]: 
        print("Waiting for cman")
    else:
        board[cman_position[0]][cman_position[1]] = 'C'
    if 255 == spirit_position[0] == spirit_position[1]:
        print("Waiting for spirit")
    else:
        board[spirit_position[0]][spirit_position[1]] = 'S' 
    print(f"Score: {40 - left_points}")
    print(f"Left lives: {3 - attempts}")
    for line in board:
        print("".join(line))


def handle_player_input(client_socket, host, port):
    """
    Handle user input for player movement or quitting the game.

    Parameters:
    client_socket (socket): The client socket.
    host (str): Server address.
    port (int): Server port.
    """
    keys = cu.get_pressed_keys(['w', 'a', 's', 'd', 'q']) #get the pressed keys


    if 'q' in keys: #if q is pressed, send a quit message to the server and exit the game
        quit_message = sl.pack_quit_User()
        client_socket.sendto(quit_message, (host, port))
        cu.clear_print("Exiting game...")
        return False  # Stop the game loop

    direction = None
    if 'w' in keys:
        direction = sl.Direction.UP
    elif 'a' in keys:
        direction = sl.Direction.LEFT
    elif 's' in keys:
        direction = sl.Direction.DOWN
    elif 'd' in keys:
        direction = sl.Direction.RIGHT

    if direction is not None:
        move_message = sl.pack_player_movement_User(direction)
        client_socket.sendto(move_message, (host, port))
    return True


if __name__ == "__main__":
    role = 'watcher'
    host = 'localhost'
    port = 1337

    if len(sys.argv) >= 3: #if the user provides the role and host
        role = sys.argv[1]
        host = sys.argv[2]

    if len(sys.argv) == 4: #if the user provides the port in addition to the role and host
        try:
            port = int(sys.argv[3])
        except ValueError:
            print("Invalid port number")
            sys.exit(1)

    if role not in ['watcher', 'cman', 'spirit']:  
        print("Invalid role")
        sys.exit(1)

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setblocking(False)  # Set non-blocking mode
        connect_to_server(client_socket, host, port, role)

        game_running = True
        while game_running: #while the game is running
            game_running = listen_to_server_non_blocking(client_socket)
            if role != 'watcher' and game_running:
                game_running = handle_player_input(client_socket, host, port)
            
    except Exception as e:
        cu.clear_print("Error:", e)
    finally:
        client_socket.close()
