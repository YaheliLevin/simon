import socket
import sys
import os
import threading
from threading import Thread, Lock
import ast
import random
from time import sleep

IP = '0.0.0.0'                                                      # IP
PORT = 8820                                                         # port (which port will be used for clients to connect and send data)
ADDR = (IP, PORT)                                                   # final address (a tuple, from the port and the IP
SIZE = 1024                                                         # size (used for recieving data)
FORMAT = "utf-8"                                                    # the format of the data when recieved

players = []                                                        # the consoles currently connected (each cell have a tuple - (connection,address) )
players_status = []                                                 # the current status of the consoles (waiting/playing/done...)

min_players_in_a_game = 2                                           # the minimum amount of players that a game will be started with

# -----global variables-----
# can be accesed from anywhere in the code

global players_ready                                                # the amount of consoles that are ready to start playing
players_ready = 0

global sequence                                                     # the sequence will be generated at the beggining of each game
sequence = []                                                     
    
global playing                                                      # tells the main when to start running the game
playing = False                                             

global clients_connected                                            # the amount of connected clients
clients_connected = 0




def handle_client (connection, address):                            # when a client is connecting to the server, a thread starts running with this def to handle the client
    print(f"[NEW CONNECTION] console {address} is connected")
    
    connected = True                                                # True while the client is connected
    
    global clients_connected                                        # state that we reffer to a global varible when using that name
    global playing                                                  # state that we reffer to a global varible when using that name
    
    while connected:                                                # while the client is connected
    
        playing_internal = False                                    # True when all players are ready
        waiting = True                                              # True when a game is not running
    
        while waiting:                                              # true until a game starts
            msg = connection.recv(SIZE).decode(FORMAT)              # recieve data from server
            print(f"[*AT WAITING* NEW DATA FROM CLIENT] {address[0]}: {msg}")
        
            if msg == "quit":                                       # if the client quits   
                
                for i in range(len(players)):                       # loop players
                    
                    if players[i] == ((connection,address)):        # find the correct client
                        players.remove(players[i])                  # remove it
                        temp = players_status[i]                    # remove the clients status too
                        players_status.remove(temp)
                        clients_connected = clients_connected - 1   # decrease clients connected by 1
                        
                        i = len(players)                            # break the loop (if it got here, its job is done)
                        connected = False                           # stop the thread
                        break
                break
            
            if msg == "ready":                                      # if the client is ready to play
                global players_ready                                #state that we reffer to a global varible when using that name
                print(f"[CONSOLE STATUS] console {address} is ready to play")
                
                for i in range(len(players_status)):                # loop players status
                    
                    if players[i] == ((connection,address)):        # find the cell refering to this client
                        print(f"[CONSOLE STATUS] {address[0]}: ready")
                        players_status[i] = "ready"                 # change its status to "ready"
                
                players_ready = players_ready + 1                   # increase players ready by 1
            
            
            if playing == True:                                     # if playing is true => a game has started
                waiting = False                                     # stop waiting for a game to start
                playing_internal = True                             # start a game (playing internal is true when the client is playing, the global playing is true when a game is running)
       
        
        while playing_internal and playing:                         # while a game is running and the client is still in that game
            
            if msg == "":                                           # prevent it from printing blank lines
                msg = connection.recv(SIZE).decode(FORMAT)          # recieve data from server
                print(f"[*AT INRERNAL* NEW DATA FROM CLIENT] {address[0]}: {msg}")
            
            if msg == "quit":                                       # if the client quits
                connected = False                                   # stop the thread
                
                for i in range(len(players)):                       # loop players
                    
                    if players[i] == (connection, address):         # find the correct client
                        players.remove(players[i])                  # remove it
                        players_status.remove(players_status[i])    # remove the clients status too
                        clients_connected = clients_connected - 1   # decrease clients connected by 1
                        
                        i = len(players)                            # break the loop
                        break
                break
            
            if msg == "done":                                       # if the client is done with the current turn
               
                for i in range(len(players)):                       # loop players
                   
                    if (players[i] == (connection, address)):       # find the correct client in the list
                        players_status[i] = "done"                  # update status to "done"    
                
                print(f"[CONSOLE STATUS] console {players[i][1]} is done with the current turn")
                msg = ""
                
            
            if msg == "lost":                                       # if the client was wrong

                for i in range (len(players)):                      # loop players
                   
                    if (players[i] == (connection, address)):       # find the correct client in the list
                        players_status[i] = "waiting"               # update status to "waiting"
                        print(f"[player lost] console {address}")
                        playing_internal = False                    # leave the current game
                
                print(f"[CONSOLE STATUS] console {players[i][1]} is out")
                msg = ""
            
            if msg == "win":                                        # if the client won
                waiting = True                                      # return to waiting
                playing_internal = False                            # leave the game
                
        waiting = True                                              # when done with playing_internal return to waiting
        playing_internal = False                                    
        
    connection.close()                                              # when the client is no longer connected - close the connection

def send_to_client(connection, msg):                                # send data to a single client
    print(f"[DATA TO CLIENT] {msg}")
    connection.send(msg.encode(FORMAT))
    
def send_to_all_clients(players,players_status, msg):               # send data to multiple clients (playing clients only)
    
    for i in range(len(players)):
        
        if players_status[i] == "ready" or players_status[i] == "playing" or players_status[i] == "done":
            send_to_client(players[i][0], msg)
    
def win_check (players, players_status):                            # check for a winner  
    
    winner = ""
    
    for i in range(len(players_status)):                            # loop player status
        
        if players_status[i] == "done":                             # if a player is done
           
           if winner == "":                                        # and there is no other player that is done
                winner = players[i]                                 # this player is the winner (still temporary until the loop is over)
            
           else:                                                   # if there is more than one player that is done with the current turn - there is no winner right now
               return -1                                           # return -1 (no winner)
    
    if winner != "":                                                # if a single winner was found
        return winner                                               # return him
    
def generateSequence(sequence):                                     # generate the sequence (adds one step to the list every time called)
    sequence = sequence
    
    if (len(sequence) >2 and                                        # prevent more than two repeats of the same button in the sequence
        sequence[len(sequence)-1] == sequence[len(sequence)-2]): 
        repeatedNumber = sequence[len(sequence)-1]  
        numList = [0,1,2,3]
        numList.remove(repeatedNumber)
        sequence.append(random.choice(numList))                     # add a number if there is a repeated number - it will choose from a list without the repeated number
        return sequence
    
    sequence.append(random.randint(0, 3))                           # add a number between 0-3 to the sequence
    return sequence                                                 # return the new sequence

def run_game ():                                                    # will run as a thread that runs the game so the code won't be stuck
    
    winner = ""                                                     # the winner
    
    global players_ready                                            # state that we reffer to a global varible when using that name
    players_ready = 0

    global playing                                                  # state that we reffer to a global varible when using that name
    playing = playing
    
    
    send_to_all_clients(players,players_status, "starting")         # send "starting" command to all playing clients
    
    while playing:                                                  # while playing the game
        
        global sequence                                             # state that we reffer to a global varible when using that name
        sequence = sequence
        
        sequence = generateSequence(sequence)                       # generate and send the sequence
        send_to_all_clients(players,players_status, str(sequence))
        
        waiting_for_players = True                                  # check that everyone that is still in the game is done playing
        while waiting_for_players:
            playing_count = 0
            
            for i in range(len(players_status)):
                
                if players_status[i] == "playing":
                    playing_count = playing_count + 1
            
            if playing_count == 0:
                print(f"[GAME STATUS] all players have finished their turn")
                waiting_for_players = False
                break
            

        all_lost_scenario = 0                                        # check if all players have lost. if so, end the game
        
        for i in range(len(players_status)):
            if players_status[i] == "waiting":
                all_lost_scenario = all_lost_scenario + 1
                
        if all_lost_scenario == len(players_status):
            sequence = []                                            # reset the sequence
            playing = False
            break


        print(f"[GAME STATUS] checking for winner")                   # run on status, check for winner
        winner = win_check (players, players_status)
        
        if winner != -1:
            print(f"[GAME STATUS] {winner[1]} has won the game!")
            playing = False
            break
        
        
        print(f"[GAME STATUS] winner not found, moving on to next turn")
        
        for i in range (len(players_status)):                         # if no winner was found
            
            if players_status[i] == "done":                           # reset "done" status to "playing" status
                players_status[i] = "playing"
        send_to_all_clients(players,players_status, "continue")       # send continue MSG to all playing clients
        sleep(0.5)
    
    
    send_to_client (winner[0], "win")                                 # if a winner was found - tell it
    sequence = []                                                     # reset the sequence
        
    for i in range (len(players_status)):                             # change all players status from done to waiting
        
        if players_status[i] == "done":
            print(f"[CONSOLE STATUS] {players[i][1]}: waiting")
            players_status[i] = "waiting"

def check_for_game_start ():                                          # running as a thread, checks for game starts

    global playing                                                    # state that we reffer to a global varible when using that name
    playing = playing 
    
    global players_ready                                              # state that we reffer to a global varible when using that name
    players_ready = players_ready
    
    while True: 
#       if there are enough players ready         and there is no other game running
        if players_ready == min_players_in_a_game and playing == False:                                        
            
            print("starting a new game")
            playing = True                                            # start a new game
            
            for i in range(len(players_status)):                      # change the status of all the players that are ready to "playing"
                
                if players_status[i] == "ready":
                    players_status[i] = "playing"
                    
            thread = Thread(target = run_game, args = ( ))
            thread.start()                                            # start the run game thread
    

def main ():
    print ("[STARTING] server is starting...")                        # start the server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print (f"[LISTENING] server started succesfuly! now listening on {IP}:{PORT}")
    
    thread = Thread(target = check_for_game_start, args = ())         
    thread.start()                                                    # start the thread that checks for game start
    
    global clients_connected                                          # state that we reffer to a global varible when using that name
    
    while True:
        
        connection, address = server.accept()                         # waiting for a new connection
        
        thread = Thread(target = handle_client, args = (connection, address))   
        thread.start()                                                # start a handle_client thread for it
        clients_connected = clients_connected + 1                     # increase clients connected by 1
        
        print(f"[ACTIVE CONNECTION] {(clients_connected)}")
        
        players.append ((connection,address))                         # add connection to players list
        players_status.append("waiting")                              # create a status for the connection
        

if __name__ == "__main__":
    main()