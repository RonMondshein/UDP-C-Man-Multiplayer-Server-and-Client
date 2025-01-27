import struct
from cman_game import Direction
FORMAT = '>B'


# Define the OPCODEs for the protocol
class OPCODE: # Operation Code
    JOIN = 0x00
    PLAYER_MOVEMENT = 0x01
    QUIT = 0x0F
    GAME_STATE_UPDATE = 0x80
    GAME_END = 0x8F
    ERROR = 0xFF


# Define the packet formats for each OPCODE
PACKET_FORMATS = {
    0x00: '>B',  # Join
    0x01: '>B',  # Player Movement
    0x0F: '',  # Quit
    0x80: '>BBBBBB5s',  # Game State Update
    0x8F: 'BBB',  # Game End
    0xFF: '>11s',  # Error
}


def pack_message_client(opcode, data) -> bytes:
    """
    binary message format include the request type from the client and the data
    Parameters:
    opcode (int): The operation code for the message.
    data (bytes): The data to be sent in the message.
    """
    return struct.pack(FORMAT, opcode) + data 


def pack_join_User(role) -> bytes:
    """"
    Pack the role of the player into a binary message.
    Parameters:
    role (str): The role of the player (cman, spirit, or watcher).
    """
    return pack_message_client(OPCODE.JOIN, role.encode('utf-8'))


def pack_player_movement_User(direction) -> bytes:
    """
    Pack the player movement direction into a binary message.
    Parameters:
    direction (Direction): The direction the player wants to move.
    """
    return pack_message_client(OPCODE.PLAYER_MOVEMENT, str(int(direction)).encode())


def pack_quit_User() -> bytes:
    """
    Pack the quit message into a binary message.
    """
    return pack_message_client(OPCODE.QUIT, b'')


def pack_game_state_update_server(state: dict) -> bytes:
    """
    Pack the game state into a binary message.
    Parameters:
    state (dict): The game state dictionary containing the following
    keys:
    - freeze (int): 0 or 1
    - c_coords (tuple[int, int]): CMan coordinates
    - s_coords (tuple[int, int]): Spirit coordinates
    - attempts (int): Number of attempts remaining
    - collected (list[int]): List representing the collected points
    returns:
    bytes: The packed binary representation of the game state.
    """
    # Extract data from the state dictionary
    freeze = state['freeze']
    c_coords = state['c_coords']
    s_coords = state['s_coords']
    attempts = state['attempts']
    collected = state['collected']
    # Validate inputs
    assert isinstance(freeze, int) and 0 <= freeze <= 1, "Freeze must be 0 or 1."
    assert len(c_coords) == 2 and all(isinstance(coord, int) and 0 <= coord < 256 for coord in c_coords), \
        "CMan coordinates must be two integers in the range [0, 255]."
    assert len(s_coords) == 2 and all(isinstance(coord, int) and 0 <= coord < 256 for coord in s_coords), \
        "Spirit coordinates must be two integers in the range [0, 255]."

    # Pack the data
    return pack_message_client(OPCODE.GAME_STATE_UPDATE, struct.pack(
            '>BBBBBB5s',
            freeze,
            c_coords[0], c_coords[1],
            s_coords[0], s_coords[1],
            attempts,
            collected  
        )
    )


def pack_game_end_server(winner, s_score, c_score) -> bytes:
    """
    Pack the game end message into a binary message.
    Parameters:
    winner (int): The winner of the game (0 for CMan, 1 for Spirit).
    s_score (int): The score of the Spirit player.
    c_score (int): The score of the CMan player.
    """
    return pack_message_client(OPCODE.GAME_END, struct.pack(
        '>BBB',
        winner,
        s_score,
        c_score
    )
)


def pack_error_server(error_code) -> bytes:
    """
    Pack the error message into a binary message.
    Parameters:
    error_code (int): The error code to be sent.
    """
    return pack_message_client(OPCODE.ERROR, struct.pack('>B', error_code))


def unpack_join_user(data: bytes) -> str:
    """
    Unpack the role of the player from a binary message.
    Parameters:
    data (bytes): The binary data containing the role of the player.
    """
    return data.decode('utf-8')


def unpack_player_movement_user(data: bytes) -> str:
    """
    Unpack the player movement direction from a binary message.
    Parameters:
    data (bytes): The binary data containing the player movement direction.
    """
    return data.decode('utf-8')



def unpack_game_state_update_server(data: bytes) -> dict:
    """
    Unpack the game state from a binary message.
    Parameters:
    data (bytes): The binary data containing the game state.
    """
    freeze, c_x, c_y, s_x, s_y, attempts, collected_bytes = struct.unpack('>BBBBBB5s', data)# Unpack the binary data

    # Convert collected_bytes into a list of 40 bits
    collected_bits = bin(int.from_bytes(collected_bytes, 'big'))[2:].zfill(40)
    collected = [int(bit) for bit in collected_bits]

    return {
        'freeze': freeze,
        'c_coords': (c_x, c_y),
        's_coords': (s_x, s_y),
        'attempts': attempts,
        'collected': collected
    }


def unpack_game_end_server(data: bytes) -> dict:
    """
    Unpack the game end message from a binary message.
    Parameters:
    data (bytes): The binary data containing the game end message.
    """
    winner, s_score, c_score = struct.unpack('>BBB', data)
    return {
        'winner': winner,
        's_score': s_score,
        'c_score': c_score
    }


def unpack_error_server(data: bytes) -> int:
    """
    Unpack the error message from a binary message.
    Parameters:
    data (bytes): The binary data containing the error message.
    """
    return struct.unpack('>B', data)[0]


