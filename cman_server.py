import socket
import sys
import shared_libary as sl
import cman_game as cg
import cman_utils as cu
import time
import select
import signal
from cman_game import Player, State, MAX_ATTEMPTS
BUFFERSIZE = 1024
cman = None
spirit = None
cman_moved = False
watchers = []


def current_state(game, address):
    """
    Generates and returns the current game state based on the board structure.

    Returns:
        dict: A dictionary containing:
            - freeze: Whether C-Man is allowed to move (1 for yes, 0 for no).
            - c_coords: Tuple representing the current coordinates of C-Man (x, y).
            - s_coords: Tuple representing the current coordinates of the Spirit (x, y).
            - attempts: Remaining lives for C-Man.
            - collected: Binary string representing collected points (1 for collected, 0 for not collected).
    """
    # Determine if C-Man can move
    freeze = 1  # Default value
    if address in watchers:
        freeze = 1
    else:
        if cman == address:
            freeze = 0 if game.can_move(Player.CMAN) else 1
        elif spirit == address:
            freeze = 0 if game.can_move(Player.SPIRIT) else 1

    # Get current coordinates for C-Man and Spirit
    c_x, c_y = game.get_current_players_coords()[Player.CMAN]
    s_x, s_y = game.get_current_players_coords()[Player.SPIRIT]

    # Remaining lives for C-Man
    attempts = MAX_ATTEMPTS - game.lives

    # Collected points status
    collected = encode_points(game)

    return {
            'freeze': freeze,
            'c_coords': (c_x, c_y),
            's_coords': (s_x, s_y),
            'attempts': attempts,
            'collected': collected
    }


def user_try_to_join(game, server_socket, message, addr):
    """
    Unpack the message and determine the role of the user, send a message back to the user
    with the game state and the role of the user.
    Parameters:
        game (Game): The current game instance.
        server_socket (socket): The server socket object.
        message (bytes): The message received from the client.
        addr (tuple): The address of the client.
    """

    role = sl.unpack_join_user(message[1:])
    global cman, spirit, watchers

    if role == 'watcher':
        watchers.append(addr)
        server_socket.sendto(sl.pack_game_state_update_server(current_state(game, addr)), addr)
    elif role == 'cman' and cman is None:
        cman = addr
        server_socket.sendto(sl.pack_game_state_update_server(current_state(game, addr)), addr)
    elif role == 'spirit' and spirit is None:
        spirit = addr
        server_socket.sendto(sl.pack_game_state_update_server(current_state(game, addr)), addr)
    else:
        error_message = sl.pack_error_server(0x01)  # Example error code
        server_socket.sendto(error_message, addr)
    
def broadcast_game_state(game, server_socket):
    """
    Sends the current game state to all watchers.
    """
    for watcher in watchers:
        state_update = sl.pack_game_state_update_server(current_state(game, watcher))
        server_socket.sendto(state_update, watcher)


def player_movement(game, server_socket, message, addr):
    """
    Unpack the message and apply the move to the player, send a message back to the user
    with the updated game state.
    Parameters:
        game (Game): The current game instance.
        server_socket (socket): The server socket object.
        message (bytes): The message received from the client.
        addr (tuple): The address of the client.
    """
    direction = sl.unpack_player_movement_user(message[1:])
    direction_int = int(direction)
    if addr == cman:
        game.apply_move(Player.CMAN, direction_int)
    elif addr == spirit:
        game.apply_move(Player.SPIRIT, direction_int)
    
    state_update = sl.pack_game_state_update_server(current_state(game, addr))
    server_socket.sendto(state_update, addr)
    broadcast_game_state(game, server_socket)


def handle_game_end(game, server_socket):
    """
    Notify all clients of the game end and restart the game after a delay.
    Parameters:
        game (Game): The current game instance.
        server_socket (socket): The server socket object.
    """
    global cman, spirit, watchers  # Declare globals at the top of the function

    winner = game.get_winner()
    game_end_message = sl.pack_game_end_server(winner, MAX_ATTEMPTS - game.lives, game.score)

    # Notify all clients repeatedly for 10 seconds
    end_time = time.time() + 10
    while time.time() < end_time:
        if cman:
            server_socket.sendto(game_end_message, cman)
        if spirit:
            server_socket.sendto(game_end_message, spirit)
        for watcher in watchers:
            server_socket.sendto(game_end_message, watcher)
        time.sleep(1)  # Send the message every second

    # Restart the game
    cman = None
    spirit = None
    watchers = []
    game.restart_game()
    print("Game restarted and server is waiting for new clients.")



def quit_game(game, server_socket, message, addr):
    """
    Remove the user from the game and notify the other user of the game end and the winner.
    Parameters:
        game (Game): The current game instance.
        server_socket (socket): The server socket object.
        message (bytes): The message received from the client.
        addr (tuple): The address of the client.
    """
    global cman, spirit, watchers
    if addr == cman:
        cman = None
        game.declare_winner(cg.Player.SPIRIT)
    elif addr == spirit:
        spirit = None
        game.declare_winner(cg.Player.CMAN)
    elif addr in watchers:
        watchers.remove(addr)


def error_server(error_code):
    """
    Generates an error message based on the error code provided.
    Parameters:
        error_code (int): The error code.
    Returns:
        bytes: The error message to be sent to the client.
    """
    return sl.pack_error_server(error_code)


FUNCTIONS = {
    sl.OPCODE.JOIN: user_try_to_join,
    sl.OPCODE.PLAYER_MOVEMENT: player_movement,
    sl.OPCODE.QUIT: quit_game,
    sl.OPCODE.GAME_STATE_UPDATE: current_state,
    sl.OPCODE.GAME_END: handle_game_end,
    sl.OPCODE.ERROR: error_server
}


def encode_points(game):
    """
    Encodes the points on the board into a compact binary format.

    Parameters:
        game (Game): The current game instance.

    Returns:
        bytes: A bytes object where each bit represents the state of a point
               (1 for uncollected, 0 for collected), packed into bytes (8 bits each).
    """
    points = list(game.get_points().keys())  # Get the list of point coordinates
    encoded_bytes = []
    curr_value = 0

    for i in range(1, len(points) + 1): 
        curr_value *= 2 # Shift left by 1 bit
        if game.get_points()[points[i - 1]] == 0:  # Check if the point is uncollected #changed_collected
            curr_value += 1 # Set the least significant bit to 1
        if i % 8 == 0:  # Pack into a byte after 8 bits
            encoded_bytes.append(curr_value) # Append the current value to the list
            curr_value = 0

    if len(points) % 8 != 0: # If the last byte is not full
        encoded_bytes.append(curr_value)

    return bytes(encoded_bytes) # Return the bytes object


def start_game(server_socket):
    """
    Starts the game server and listens for incoming messages from clients.
    Parameters:
        server_socket (socket): The server socket object.
    """

    game = cg.Game("map.txt")
    if game is None:
        print("Error: Could not load game.")
        return

    def handle_client_message(message, addr):
        """
        Handles a message received from a client.
        Parameters:
            message (bytes): The message received from the client.
            addr (tuple): The address of the client.
        """
        # Unpack the message and determine the opcode
        opcode = message[0]
        # Call the appropriate function based on the opcode
        if opcode == sl.OPCODE.JOIN:
            user_try_to_join(game, server_socket, message, addr)
        elif opcode == sl.OPCODE.PLAYER_MOVEMENT:
            player_movement(game, server_socket, message, addr)
        elif opcode == sl.OPCODE.QUIT:
            quit_game(game, server_socket, message, addr)
        elif opcode == sl.OPCODE.GAME_END:
            handle_game_end(game, server_socket)
        else:
            error_message = sl.pack_error_server(0xFF)  # Unknown opcode
            server_socket.sendto(error_message, addr)

    while True:  # Main server loop
        try:
            # Use select to wait for socket activity with a timeout
            readable, _, _ = select.select([server_socket], [], [], 1.0)
            if server_socket in readable:
                message, addr = server_socket.recvfrom(BUFFERSIZE)
                handle_client_message(message, addr)

                if cman and spirit and game.state == State.WAIT:
                    game.next_round()
                elif game.state == State.WIN:
                    handle_game_end(game, server_socket)
                    game.restart_game()

        except Exception as e:
            cu.clear_print(f"Error: {e}") 

# Graceful shutdown function
def handle_sigint(signal_number, frame):
    print("\nServer is shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    host = 'localhost'
    port = 1337
    signal.signal(signal.SIGINT, handle_sigint)

    if len(sys.argv) == 2: # If only the port number is provided
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number")
            sys.exit(1)
    if len(sys.argv) > 3:
        print("wrong number of arguments")
        sys.exit(1)
    try:
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soc.bind((host, port))
        start_game(soc)
        
    except socket.error as e:   
        print("Error: ", e)
        sys.exit(1)
        