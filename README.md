# UDP C-Man Multiplayer Server and Client  

This repository contains the **server-client communication layer** for a multiplayer version of the classic Pac-Man game. The implementation is based on **UDP protocol** and supports real-time updates, role-based gameplay, and a custom message protocol. The game logic was provided as part of the assignment, while the communication, synchronization, and client-server interaction were developed from scratch.  

---

## Features  

- **Roles**:  
  - **C-Man**: Collect points and avoid the Spirit.  
  - **Spirit**: Chase and eliminate C-Man.  
  - **Watchers**: Observe the game in real-time.  

- **Efficient Communication**:  
  - Custom binary protocol for minimal overhead.  
  - Supports real-time game state updates to all clients.  

- **Custom Protocol**:  
  - Role assignment, movement commands, and game state updates are handled with distinct opcodes for efficient parsing.  

---

## How It Works  

- The **Server** manages player roles, game states, and synchronizes updates to all connected clients.  
- **Clients** interact with the server to either play as C-Man or Spirit or spectate as Watchers.  
- Players use keyboard controls to move (`W`, `A`, `S`, `D`) or quit the game (`Q`).  

---

## File Structure  

- `cman_server.py`: Implements the UDP-based server handling game state, client roles, and updates.  
- `cman_client.py`: Implements the UDP-based client for players and watchers to connect and interact.  
- `shared_libary.py`: Handles the packing and unpacking of binary messages for server-client communication.  
- `cman_game.py`: Core game logic, provided as part of the assignment.  
- `cman_game_map.py`: Validates and loads the game map.  
- `cman_utils.py`: Utility functions for keyboard inputs and terminal management.  
- `map.txt`: Default map file for the game.  

---

## How to Run the Project

### Server
Run the server script:
- python cman_server.py -p <port>
- -p <port>: Optional parameter specifying the port to bind. Defaults to 1337.

### Client
Run the client script:
- python cman_client.py <role> <server_address> -p <port>
- <role>: Role of the client (cman, spirit, or watcher).
- <server_address>: IP address or hostname of the server.
- -p <port>: Optional parameter specifying the server's port. Defaults to 1337.

---

### Game Rules 
The map is a rectangular grid where:

Walls (W) block movement.
Points (P) are collectible items.
Free spaces (F) are passable tiles.
Starting positions for C-Man and the Spirit are marked by C and S, respectively.

The objective:

C-Man: Collect all 32 points without being caught by the Spirit.
Spirit: Catch C-Man three times to win.

---

### Dependencies
- Python 3.x
- Libraries: pynput

---

