import RPi.GPIO as GPIO
from time import sleep
import random
import sys
import os
import socket
import pygame
import ast


def main():
#Button and LED GPIO ports (by BCM):
    #redLED = 20
    #greenLED = 21
    #yellowLED = 12
    #blueLED = 16
    #redBTN = 19
    #greenBTN = 26
    #yellowBTN = 6
    #blueBTN = 13
    
    LED = [12, 21, 20, 16]                                          # LED GPIO ports
    BTN = [6, 26, 19, 13]                                           # button GPIO ports
    sequence = []                                                   # the current game sequence
   
    GPIO.setmode(GPIO.BCM)                                          # set board GPIO to BCM mode - read the numbers in the arrays as a GPIO pin number
    
    for i in range (4):                                             # setup GPIO pins as INPUT for buttons and OUTPUT for LEDS
        
        GPIO.setup(LED[i], GPIO.OUT)                                # set LED pins to be output pins
        GPIO.setup(BTN[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)       # Set BTN pins to be input pins and set initial value to be pulled HIGH (off)
        GPIO.output(LED[i], 0)
    
    
    print("client start")                                           # setup the client socket
    client_socket = socket.socket()
    client_socket.connect(('10.100.102.29', 8820))
    print("connected to server")
    
    running = True                                                  # boolean that is true while the code is running
    between_games = True                                            # boolean that is true while not in a game
    waiting_for_others = False                                      # boolean that is true while waiting for other players to finish their turn
    choice_sent = False                                             # boolean that is true when the user is waiting for a game to start
    first_time = True                                               # boolean that is true when playing for the first time
    
    try:
        while running:                              
            
            while between_games:                                    # enters while when not currently playing
                
                print(f"[STATUS] between games")
                
                if first_time:                                      # enters when the code runs for the first time (different sound instructions)
                    play_sound ("start_msg")                        # first time sound : instructions - green means ready, red means exit
                
                else:                                               # enters when it already played one game or more (different voice instructions)
                    play_sound ("play_again_msg")                   # play again sound : instructions - green means ready, red means exit
                
                ans = BTNpress(BTN)                                 # recieve user input 
                print("user answer: " + str(ans))
                
                if ans == 1:                                        # green button => start a game
                    send_to_server("ready", client_socket)          # send to server that the player is ready
                    choice_sent = True                              # enter choise sent loop
               
                elif ans == 2:                                      # red button => quit
                    send_to_server("quit", client_socket)           # send to server that the client has decided to quit
                    running = False                                 # stop running loop                         
                    quit(client_socket)                             # close the socket, clean GPIO
                
                else:                                               # if the user pressed yellow/blue
                    play_sound("illegal_command")                   # play illegal command sound
                    sleep(2)
               
                while choice_sent:                                  # enters when the user is ready and waiting for a game to start
                    first_time = False                              
                    data = receive_from_server(client_socket)       # wait for data from server that the game is startswith
                        
                    if data == "starting":                          # if a game is starting
                        choice_sent = False                         # reset choise sent for next time
                        between_games = False                       # make between game false (will be false until the current game is over)
                        play_sound("starting_msg")                  # play starting sound ("are you ready? the game will start in 3...2...1...")
                        sleep(5.2)
                        break
            
            sequence = receive_from_server(client_socket)           # recieve the sequence from server (the server will add one step each turn)
            sequence = ast.literal_eval(sequence)                   # convert the sequence back to list using ast library (it's sent as a string)
            show_sequence(sequence,LED)                             # show the sequence to the player   
            lose = recieve_player_sequence(sequence, LED, BTN)      # call recieve sequence, the bollean "lose" is lose if the player had a mistake
            print("lose: " + str(lose))
           
            if lose == True:                                        # if the player lost
                send_to_server("lost", client_socket)               # send to server that the console is out of the game
                play_sound("lose")                                  # play lose sound
                waitForRelease(BTN)                                 # wait for button release to convert double press
                sleep(2)
                
                between_games = True                                # back to main menu
                
            else:                                                   # if the player repeated the sequence correctly
                send_to_server("done", client_socket)               # send to server that the player is done
            
                waiting_for_others = True                           # true when the has passed to the next turn and waiting for other players to finish
                
                while waiting_for_others:                           # while waiting for players to finish their turn
                    data = receive_from_server(client_socket)       # recieve data from server
                
                    if data == "continue":                          # moving to next turn
                        print("moving to next turn")
                        waiting_for_others = False                  # break the loop
                        break
                    
                    if data == "win":                               # if this is the only player left that did the turn correctly
                        win(LED)                                    # play win sound and lights
                        send_to_server("win", client_socket)        # let the "handle_client" def in the server now that its client won
                    
                        waiting_for_others = False                  # back to main menu
                        between_games = True

            
    except Exception as e:                                          # if there is an exeption, print the type and the line
        print(str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        quit(client_socket)                                         # shut down correctly (close the socket, clean GPIO)


   

def quit (client):                                                  # quit the code
    send_to_server ("quit",client)                                  # inform server
    client.shutdown(socket.SHUT_RDWR)                               # shut down client
    client.close()                                                  # close the client
    play_sound("exit")                                              # play exit game sound
    sleep(1.5)
    pygame.quit()                                                   # quit pygame (used as a sound player)
    GPIO.cleanup()                                                  # clean GPIO (back to default)
    sys.exit()                                                      # quit


def show_sequence (sequence,LED):                                   # display the given sequence with the correct LEDs
    
    for i in range (len(sequence)):                                 # loop on the whole array
        temp = int(sequence[i])
        GPIO.output(LED[temp], 1)                                   # turn on LED by the number in sequence
        play_sound(str(temp))                                       # play the correct sound
        sleep(0.5)                                                  # stay on for half a second
        GPIO.output(LED[temp], 0)                                   # turn of the LED
        sleep(0.5)                                                  # stay off for half a second before displaying the next one
   
def recieve_player_sequence (sequence,LED, BTN):                    # recieve the player's repeat to the given sequence.
    print("recieve sequence")
    
    for i in range(len(sequence)):                                  # run one time for each press
        userInput = BTNpress(BTN)                                   # wait until a button is pressed and save the button number
        GPIO.output(LED[userInput], 1)                              # turn on the button's LED
        
        if (userInput is not sequence[i]):                          # if the user is wrong:
            GPIO.output(LED[userInput], 0)                          # turn off the button's LED
            return True                                             # return True => the user is wrong
        
        play_sound(str(userInput))                                  # if the user is right, play the button's sound
        waitForRelease(BTN)                                         # wait for the button to be released before passing to the next step
        sleep(0.5)                                                  # the button takes time to go up, so sleep prevents recieving another click on the button before its fully released
        GPIO.output(LED[userInput], 0)                              # turn off the button's LED
        
    sleep(1)                                                        # sleep before showing the next sequence
    return False
     
     
def win (LED):                                                      # blink all LEDS 4 times and play win sound
    
    play_sound("win")
    
    for i in range (4):
        GPIO.output(LED[0], 1)                                      # turn on all LEDs
        GPIO.output(LED[1], 1)
        GPIO.output(LED[2], 1)
        GPIO.output(LED[3], 1)
        sleep(0.3)                                                  # stay on for 0.3 seconds
        GPIO.output(LED[0], 0)                                      # turn off all LEDs
        GPIO.output(LED[1], 0)
        GPIO.output(LED[2], 0)
        GPIO.output(LED[3], 0)
        sleep(0.3)                                                  # stay off for 0.3 seconds

def BTNpress (BTN):                                                 # return which button was pressed
    while True:
        if (GPIO.input(BTN[0]) == False):
            return 0                                                # yellow
        if (GPIO.input(BTN[1]) == False):
            return 1                                                # green
        if (GPIO.input(BTN[2]) == False):
            return 2                                                # red
        if (GPIO.input(BTN[3]) == False):
            return 3                                                # blue

def waitForRelease(BTN):                                            # wait for all buttons to be released to prevent double clicks
    running = True
    while running:
        if (GPIO.input(BTN[0]) == True and 
            GPIO.input(BTN[1]) == True and 
            GPIO.input(BTN[2]) == True and 
            GPIO.input(BTN[3]) == True):
            running = False

def play_sound (file_name):                                         # play sounds needed for the game by name/number   
    pygame.mixer.init()
    basefolder =  r'/home/pi/Desktop/simon'                         # the folder where all the sound files are located
    finalLocation = basefolder + "//" + str(file_name) + '.wav'     # build the final path to the sound file with the name that the function was called with
    current_sound = pygame.mixer.Sound(finalLocation)               # save as a mixer sound variable
    current_sound.play()                                            # play the sound
    print (f"[PLAY SOUND] {file_name}")
    
def receive_from_server(client_socket):                             # recieve data from server and return it
    data = client_socket.recv(1024)
    print(f"[NEW DATA FROM SERVER] {data.decode('utf-8')}")
    return (data.decode('utf-8'))


def send_to_server(data, client_socket):                            # send data to server
    client_socket.send(data.encode('utf-8'))
    print(f"[DATA SENT] {data}")
    
    
    
    
if __name__ == '__main__':
    main()