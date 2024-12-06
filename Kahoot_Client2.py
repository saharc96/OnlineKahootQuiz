
import socket
import threading
import time
import sys
import select
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# Generate a key and IV (Initialization Vector)
key = b'\x04\x03|\xeb\x8dSh\xe0\xc5\xae\xe5\xe1l9\x0co\xca\xb1"\r-Oo\xbaiYa\x1e\xd1\xf7\xa2\xdf'
iv = b'#\xb59\xee\xa7\xc4@n\xe5r\xac\x97lV\xff\xf1'

# Function to encrypt plaintext using AES-CBC
def encrypt(plaintext):
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode(FORMAT)) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext

# Function to decrypt ciphertext using AES-CBC
def decrypt(ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
    return decrypted_data.decode(FORMAT)

# Function to start the client
def start_thread():
    """
    This function starts the threads that receives and sends messages
    between the clients in that particular group chat.
    param approve_orNot: the message that the server sends to the client to notify him
                          if he was approved to join the group chat or to existing group chat
    return: nothing
    """
    # Print the message from the server
    # Starting Threads For Listening And Writing
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()

    # join the threads
    receive_thread.join()
    write_thread.join()

    print("Exiting the server... Good bye!")
    return


def receive():
    """
    This function receives messages from the server (a.k.a from other clients in the group)
    and prints them to the screen.
    return: nothing
    """
    while True:
        try:
            # Receive Message From Server
            message = client.recv(1024).decode(FORMAT)
            # message = decrypt(client.recv(1024))
            # print the message to the screen
            sys.stdout.write('\r' + message)
            sys.stdout.flush()

            # check if the message is the last message
            if "The game is over!" in message:
                client.close()
                # set the event
                game_over.set()
                break
            time.sleep(4)
        except:
            # Close Connection When Error
            print("An error occurred! , closing the connection")
            client.close()
            break
    return


def write():
    """
    This function gets a question from the server and sends the answer back
    """
    while True:
        try:
            # check if the game is over
            if game_over.is_set():
                break

            # use select to wait until there is data ready to be read on sys.stdin
            ready_to_read, _, _ = select.select([sys.stdin], [], [], 1.5)
            if ready_to_read:
                # get the answer from the user
                answer = input()
                # check that answer is a number
                while not answer.isnumeric():
                    sys.stdout.write('\r' + "Invalid input, please try again\n")
                    sys.stdout.flush()
                    answer = input()

                answer = int(answer)
                # check client entered a number between 1-4
                while answer < 1 or answer > 4:
                    sys.stdout.write('\r' + "Invalid input, please try again\n")
                    sys.stdout.flush()
                    answer = input()
                # send the answer to the server
                client.send(str(answer).encode(FORMAT))
                # client.send(encrypt(str(answer)))
        except:
            # Close Connection When Error
            print("An error occurred! , closing the connection")
            client.close()
            break
    return


def init_dialogue():
    """
    This function is the first dialogue that the client has with the server.
    In this dialogue the client will choose if he wants to create a new group chat,
    join an existing one or exit the program.
    return: nothing
    """
    global clientsNameS
    # The server sends initial dialogue messages
    # init_msg = client.recv(1024).decode(FORMAT).strip()
    init_msg = decrypt(client.recv(1024))
    # The client receives the messages and prints them to the screen
    print(init_msg)

    while True:
        # The client get the choose option message from the server
        # init_msg = client.recv(1024).decode(FORMAT).strip()
        init_msg = decrypt(client.recv(1024))
        print(init_msg)

        if "Please enter your choice:" in init_msg:
            choice = input("enter your choice: ")
            # The client sends the user's choice to the server
            # client.send(choice.encode(FORMAT))
            client.send(encrypt(choice))
            # The server handles the user's choice
            if choice == "1":
                # server asks for name:
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter your name:" in init_msg:
                    # print(init_msg)
                    clientsNameS = input(init_msg)
                    # client.send(clientsNameS.encode(FORMAT))
                    client.send(encrypt(clientsNameS))
                    # print("Check: SENDED THE NAME TO SERVER")
                # server asks for ID:
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter the quiz id:" in init_msg:
                    print(init_msg)
                    quizID = input()
                    # client.send(quizID.encode(FORMAT))
                    client.send(encrypt(quizID))

                # server asks for password:
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter the password:" in init_msg:
                    print(init_msg)
                    password = input()
                    # client.send(password.encode(FORMAT))
                    client.send(encrypt(password))

                break

            elif choice == "2":
                # server asks for name:
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter your name:" in init_msg:
                    print(init_msg)
                    clientsNameS = input()
                    # client.send(clientsNameS.encode(FORMAT))
                    client.send(encrypt(clientsNameS))
                # server asks for password:
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter a password:" in init_msg:
                    print(init_msg)
                    password = input()
                    # client.send(password.encode(FORMAT))
                    client.send(encrypt(password))

                # server asks for category:
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter the category of the quiz:" in init_msg:
                    print(init_msg)
                    category = input()
                    # client.send(category.encode(FORMAT))
                    client.send(encrypt(category))
                    while True:
                        # get the chosen category/error message
                        # init_msg = client.recv(1024).decode(FORMAT).strip()
                        init_msg = decrypt(client.recv(1024))
                        if "Invalid category. Please try again." in init_msg:
                            print(init_msg)
                            category = input()
                            # client.send(category.encode(FORMAT))
                            client.send(encrypt(category))
                        else:
                            print(init_msg)
                            break

                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Please enter the number of participants:(1-9)" in init_msg:
                    print(init_msg)
                    num_of_participants = int(input())
                    while True:
                        if 1 <= int(num_of_participants) <= 9:
                            # client.send(str(num_of_participants).encode(FORMAT))
                            client.send(encrypt(str(num_of_participants)))
                            break
                        else:
                            print("You need to enter only 1-9, please enter again:")
                            num_of_participants = input()

                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Your quiz ID is:" in init_msg:
                    print(init_msg)
                    print()

                break

            elif choice == "3":
                # init_msg = client.recv(1024).decode(FORMAT).strip()
                init_msg = decrypt(client.recv(1024))
                if "Exiting the server..." == init_msg:
                    print(init_msg)
                    client.close()
                    return
            else:
                print("Invalid input, please try again")

    # print("broke free")
    # check if the group exists and server accepts the client
    # approve_orNot = client.recv(1024).decode(FORMAT).strip()
    approve_orNot = decrypt(client.recv(1024))
    print(approve_orNot)
    if "Kahoot quiz created successfully!" in approve_orNot:
        start_thread()
    elif "You have joined the khaoot quiz!" in approve_orNot:
        start_thread()
    else:
        # error_msg = client.recv(1024).decode(FORMAT).strip()
        error_msg = decrypt(client.recv(1024))
        print(error_msg)
        print("Exiting the server... Good bye!")
        client.close()
        return



if __name__ == "__main__":
    # Choosing Nickname
    clientsNameS = ""
    # Connecting To Server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 8009))
    FORMAT = 'utf-8'  # Define the encoding format of messages from client-server
    # Create an Event object
    game_over = threading.Event()
    # Start the dialogue
    init_dialogue()
