
import socket
import threading
import time
from Kahoot_DataBase import QuizDataBase
from copy import deepcopy
import sys
import queue
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


# Sending Messages To All Connected Clients
def broadcast(client, message, quiz_id):
    """
    This function sends a message to all the clients in the group chat.
    param client: the socket object of the client
    param message: the message to send
    param quiz_id: the group id of the group chat
    return: nothing
    """
    global quiz_db
    try:
        client.send(message)
        # client.send(encrypt(message))
    except Exception as e:
        print(e)
        client.close()
        # get the index of the client from the list
        index = None
        for client_tuple in quiz_db.quizes[quiz_id]['Clients']:
            if client_tuple[1] == client:
                index = int(quiz_db.quizes[quiz_id]['Clients'].index(client_tuple))
                # update the number of clients in the game
                quiz_db.quizes[quiz_id]['CurrentNumParticipents'] -= 1
                quiz_db.quizes[quiz_id]['ExcpectedNumParticipents'] -= 1
                # remove the client tuple from the list
                quiz_db.quizes[quiz_id]['Clients'].pop(index)
                break

def waiting_room(client, quiz_id):
    """
    This function waits for all the clients to Kahoot quiz to connect.
    param client the socket object of the client
    param quiz_id: the id of the quiz
    return: nothing
    """
    global quiz_db

    while True:
        # sent all clients in the waiting room how many clients are connected
        # and how many are missing
        message = (f'Connected: {quiz_db.quizes[quiz_id]["CurrentNumParticipents"]} / '
                   f'{quiz_db.quizes[quiz_id]["ExcpectedNumParticipents"]}\n')
        time.sleep(0.5)
        # broadcast the message to all the clients
        broadcast(client, message.encode(FORMAT), quiz_id)
        # broadcast(client, message, quiz_id)
        time.sleep(1.5)

        if quiz_db.quizes[quiz_id]['CurrentNumParticipents'] == quiz_db.quizes[quiz_id]['ExcpectedNumParticipents']:
            # send all the clients that the game is about to start
            message = "The game is about to start!\n"
            broadcast(client, message.encode(FORMAT), quiz_id)
            # broadcast(client, message, quiz_id)
            break


def game(client, quiz_id):
    """
    This function runs the quiz game.
    param client: the socket object of the client
    param quiz_id: the id of the quiz
    """
    global quiz_db

    questions = quiz_db.quizes[quiz_id]['Questions']
    answers = quiz_db.quizes[quiz_id]['Answers']

    # get the player index from the list
    player_index = None
    for client_tuple in quiz_db.quizes[quiz_id]['Clients']:
        if client_tuple[1] == client:
            player_index = int(quiz_db.quizes[quiz_id]['Clients'].index(client_tuple))
            break
    # print("Player index is:", player_index)

    # measure the time it takes for the clients to answer the question
    time_to_answer = 0
    max_time_to_answer = 15 # seconds

    for question, answer in zip(questions, answers):
        # send the question concatenated with the answers to all the clients
        message = (f'{question}\n'
                   f'1. {answer[0]}\n2. {answer[1]}\n3. {answer[2]}\n4. {answer[3]}\n')
        broadcast(client, message.encode(FORMAT), quiz_id)
        # broadcast(client, message, quiz_id)
        time.sleep(0.5)

        # start counting the time
        start_time = time.time()
        # wait for the clients to answer
        try:
            client.settimeout(max_time_to_answer)
            client_answer = client.recv(1024).decode(FORMAT).strip()
            # client_answer = decrypt(client.recv(1024))
            print('Client answered:', client_answer)
        except socket.timeout:
            client_answer = -1
            print("Out Of Time :(")
        except:
            print("An error occurred! , closing the connection")
            client.close()
            break

            # stop counting the time
        time_to_answer = time.time() - start_time
        start_time = 0  # reset timer
        # if the client didn't answer in time
        if time_to_answer >= max_time_to_answer:
            # send the client that his answer is incorrect
            client.send("Out Of Time :(\n".encode(FORMAT))
            # client.send(encrypt("Out Of Time :(\n"))
            continue
        else:
            # check if the answer is correct
            if quiz_db.score_quiz(client, int(client_answer), quiz_id, time_to_answer):
                # send the client that his answer is correct
                client.send("Correct!\n".encode(FORMAT))
                # client.send(encrypt("Correct!\n"))
            else:
                # send the client that his answer is incorrect
                client.send("Incorrect!\n".encode(FORMAT))
                # client.send(encrypt("Incorrect!\n"))

        # print the player score
        score_board = print_game_score_1player(quiz_id, player_index)
        broadcast(client, score_board.encode(FORMAT), quiz_id)
        # broadcast(client, score_board, quiz_id)

    sem.acquire()
    # inc the number of finished players
    quiz_db.quizes[quiz_id]['NumOfFinishedPlayers'] += 1
    sem.release()

    # pool until all the clients finish the game
    while quiz_db.quizes[quiz_id]['NumOfFinishedPlayers'] < quiz_db.quizes[quiz_id]['ExcpectedNumParticipents']:
        pass

    # print the final score
    score_board = print_game_score(quiz_id, status='ENDED')
    broadcast(client, score_board.encode(FORMAT), quiz_id)
    # broadcast(client, score_board, quiz_id)
    time.sleep(0.5)

    # send the clients that the game is over and the results
    message = "The game is over!\n"
    broadcast(client, message.encode(FORMAT), quiz_id)
    # broadcast(client, message, quiz_id)
    time.sleep(0.5)

    # close the connection
    client.close()
    return quiz_id


def print_game_score_1player(quiz_id, player_index, status='Active'):
    """
    This function prints the game score to 1 player only.
    param quiz_id: the id of the quiz
    param player_index: the index of the player in the list of clients
    param status: the status of the game
    """
    global quiz_db
    if status == 'Active':
        # send the current game score to all the clients
        score_board = '############################\n'
        # for cind, (name, _, score) in enumerate(quiz_db.quizes[quiz_id]['Clients']):
        #     if cind < 1:
        #         score_board += f'{cind + 1}. {name}: {score}\n'
        # get the player score using the index
        score_board += f'Your score: {quiz_db.quizes[quiz_id]["Clients"][player_index][2]}\n'
        score_board += '############################\n'
        return score_board

def print_game_score(quiz_id, status='Active'):
    """
    This function prints the game score to all the clients.
    param quiz_id: the id of the quiz
    param status: the status of the game
    """
    global quiz_db
    if status == 'Active':
        # send the current game score to all the clients
        score_board = '############################\n'
        for cind, (name, _, score) in enumerate(quiz_db.quizes[quiz_id]['Clients']):
            if cind < 3:
                score_board += f'{cind + 1}. {name}: {score}\n'

        score_board += '############################\n'
        return score_board
    elif status == 'ENDED':
        # send the final game score to all the clients
        score_board = '########-FINAL SCORE-########\n'
        for cind, (name, _, score) in enumerate(quiz_db.quizes[quiz_id]['Clients']):
            if cind < 3:
                score_board += f'{cind + 1}. {name}: {score}\n'

        score_board += '############################\n'
        return score_board


# Handling Messages From Clients
def handle(client, quiz_id):
    """
    This function handles the messages from the clients.
    param client: the socket of the client
    param group_id: the group id of the group chat
    return: nothing
    """
    global quiz_db

    if quiz_id == -1:
        client.send(encrypt("Error with password/group id."))
        return

    # Wait in the waiting room until all the clients are connected
    waiting_room(client, quiz_id)
    game(client, quiz_id)

    return quiz_id

# _______________________________________

def init_dialogue(client):
    """
    This function initializes the dialogue with the client.
    In this function, the client is asked to create, join a group chat or exit the server.
    param client: the socket of the client
    return: the group id of this client if he chose to create/join a group chat.
    """
    global quiz_db
    # client.send("Welcome to the Kahoot quiz Server!\n"
    #             "Please choose an option:\n"
    #             "1. Join an existing Kahoot quiz\n"
    #             "2. Create a new Kahoot quiz\n"
    #             "3. Exit\n".encode(FORMAT))
    client.send(encrypt("Welcome to the Kahoot quiz Server!\n"
                "Please choose an option:\n"
                "1. Join an existing Kahoot quiz\n"
                "2. Create a new Kahoot quiz\n"
                "3. Exit\n"))
    time.sleep(1)
    while True:
        # client.send("Please enter your choice: ".encode(FORMAT))
        client.send(encrypt("Please enter your choice: "))
        # choice = client.recv(1024).decode(FORMAT).strip()
        choice = decrypt(client.recv(1024))
        print(choice)
        if choice == "1":
            group_id = join_kahoot_quiz(client)
            break
        elif choice == "2":
            group_id = create_khaoot_quiz(client)
            break
        elif choice == "3":
            # client.send("Exiting the server...".encode(FORMAT))
            client.send(encrypt("Exiting the server..."))
            client.close()
            exit()
        else:
            print("Invalid choice. Please try again.")

    return int(group_id)


# _______________________________________


def create_khaoot_quiz(client):
    """
    This function creates a new group chat if the client chooses so.
    param client: the socket of the client
    return: the group id of the new group chat
    """
    global quiz_db
    nickname = ''
    # ask for name:
    # client.send("Please enter your name:".encode(FORMAT))
    client.send(encrypt("Please enter your name:"))
    # nickname = client.recv(1024).decode(FORMAT).strip()
    nickname = decrypt(client.recv(1024))
    print("Client name is: {}".format(nickname))
    # ask for password:
    # client.send("Please enter a password:".encode(FORMAT))
    client.send(encrypt("Please enter a password:"))
    # password = client.recv(1024).decode(FORMAT).strip()
    password = decrypt(client.recv(1024))
    print("Password is: {}".format(password))
    quiz_db.update_password(password)

    # ask for quiz category:
    # client.send("Please enter the category of the quiz:\n"
    #             "1. Math\n"
    #             "2. Capital Cities\n"
    #             "3. Physics\n".encode(FORMAT))
    client.send(encrypt("Please enter the category of the quiz:\n"
                "1. Math\n"
                "2. Capital Cities\n"
                "3. Physics\n"))
    while True:
        # category = client.recv(1024).decode(FORMAT).strip()
        category = decrypt(client.recv(1024))
        # check which category the client chose:
        if category == "1":
            category = "Math"
            # send the chosen category to the client:
            # client.send("You chose Math.".encode(FORMAT))
            client.send(encrypt("You chose Math."))
            break
        elif category == "2":
            category = "Capital_Cities"
            # send the chosen category to the client:
            # client.send("You chose Capital Cities.".encode(FORMAT))
            client.send(encrypt("You chose Capital Cities."))
            break
        elif category == "3":
            category = "Physics"
            # send the chosen category to the client:
            # client.send("You chose Physics.".encode(FORMAT))
            client.send(encrypt("You chose Physics."))
            break
        else:
            # client.send("Invalid category. Please try again.".encode(FORMAT))
            client.send(encrypt("Invalid category. Please try again."))
    print("Category is: {}".format(category))

    # ask the client of the number of participants:
    # client.send("Please enter the number of participants:(1-9)".encode(FORMAT))
    client.send(encrypt("Please enter the number of participants:(1-9)"))
    # num_of_participants = client.recv(1024).decode(FORMAT).strip()
    num_of_participants = decrypt(client.recv(1024))
    print("number of participants is:", num_of_participants)
    # update the number of participants in the database:
    quiz_db.set_num_of_participants(int(num_of_participants))

    quiz_id = quiz_db.return_current_id()
    print("client is:", client)
    # Update the group chat database:
    quiz_db.add_client(nickname, client)
    # load the quiz according to the category:
    quiz_db.add_quiz(category + '.txt')
    # notify client of group id:
    # client.send("Your quiz ID is: {}".format(quiz_id).encode(FORMAT))
    client.send(encrypt("Your quiz ID is: {}".format(quiz_id)))
    time.sleep(0.1)
    # notify client of success:
    # client.send("Kahoot quiz created successfully!".encode(FORMAT))
    client.send(encrypt("Kahoot quiz created successfully!"))

    return quiz_db.quizes[quiz_id]["QuizId"]


# _______________________________________

def join_kahoot_quiz(client):
    """
    This function joins a client to an existing group chat if the client chooses so.
    param client: the socket of the client
    return: group id of the group chat the client joined
    """
    global quiz_db
    # ask for name:
    # client.send("Please enter your name:".encode(FORMAT))
    client.send(encrypt("Please enter your name:"))
    # nameOfClient = client.recv(1024).decode(FORMAT).strip()
    nameOfClient = decrypt(client.recv(1024))
    print("Client name is: {}".format(nameOfClient))
    #print("GOT THE NAME")
    # ask for group id:
    # client.send("Please enter the quiz id:".encode(FORMAT))
    client.send(encrypt("Please enter the quiz id:"))
    #print('ASKED FOR ID')
    # quizID = client.recv(1024).decode(FORMAT).strip()
    quizID = decrypt(client.recv(1024))
    print("Quiz ID is: {}".format(quizID))

    # client.send("Please enter the password:".encode(FORMAT))
    client.send(encrypt("Please enter the password:"))
    # password = client.recv(1024).decode(FORMAT).strip()
    password = decrypt(client.recv(1024))
    print("Password is: {}".format(password))
    time.sleep(0.5)

    print("CHECK: ", quiz_db.quizes)
    # check if group id exists:
    for quiz in quiz_db.quizes:
        #print("CHECK: ", quiz['QuizId'])
        if quiz['QuizId'] == int(quizID):
            print("Quiz exists.")
            if quiz['Password'] == password:
                print("Password is correct.")
                # add client to the group chat:
                quiz['Clients'].append((nameOfClient, client, 0))
                # inc the number of participants:
                quiz['CurrentNumParticipents'] += 1
                # delay to allow client to receive message:
                time.sleep(1)
                # notify client of success:
                # client.send("You have joined the khaoot quiz!".encode(FORMAT))
                client.send(encrypt("You have joined the khaoot quiz!"))
                print("CHECK: ", quiz_db.quizes)
                return quizID
            time.sleep(1)

    # notify client of incorrect password:
    # client.send("Wrong password/ID!\n".encode(FORMAT))
    client.send(encrypt("Wrong password/ID!\n"))
    return "-1"

def init_handle_client(client_soc_obj):
    """
    This function handles the client.
    param client_soc_obj: the socket object of the client
    return: True if the client was accepted, False otherwise
    """
    global quiz_db, isAccepted
    # Call the initialization dialogue function:
    quiz_id = init_dialogue(client_soc_obj)
    # if it is -1, the client entered wrong group id or password
    if quiz_id == "-1":
        # client_soc_obj.send("Error with password/group id. "
        #                     "Reconnect and try again...".encode(FORMAT))
        client_soc_obj.send(encrypt("Error with password/group id. "
                            "Reconnect and try again..."))
        client_soc_obj.close()
        return
    else:
        # lock the semaphore
        sem.acquire()
        # push quiz id into a queue
        quiz_id_queue.put(quiz_id)

        # release the semaphore
        sem.release()
        # print("put quiz id in queue")
        # handle_thread = threading.Thread(target=handle, args=(client_soc_obj, quiz_id))
        # handle_thread.start()
        # handle_thread.join()
        return

# _______________________________________
# Start Server Function
def start_server():
    """
    This function starts the server and listens for clients.
    if a client connects, it handles it,
    broadcast to all other members that he/she joined
    and creates a new thread for that client.
    :return: nothing
    """
    global quiz_db, isAccepted, quiz_id_queue

    while True:
        print("Server is starting...")
        # The server is listening for new connections
        print("Server is listening")
        # Accept Connection
        client_soc_obj, address = server.accept()
        print("New Client connected with {}".format(str(address)))
        print("Number of clients connected: {}".format(threading.active_count()))

        # Handle the client by starting a new thread
        client_thread = threading.Thread(target=init_handle_client, args=(client_soc_obj,))
        client_thread.start()

        # insert the thread into the queue
        sem2 = threading.Semaphore()
        sem2.acquire()
        threads_queue.put(client_thread)
        sem2.release()

        # print("check: got here")

        # start a worker thread to wait for clients to finish the setup thread and start the game
        worker_thread = threading.Thread(target=check_client_threads,  args=(client_soc_obj,))
        worker_thread.start()


def check_client_threads(client_soc_obj):
    while True:
        # Get a client thread from the queue
        client_thread = threads_queue.get()

        # Wait for the client thread to finish
        client_thread.join()

        # Remove the client thread from the queue
        threads_queue.task_done()

        # open a thread to the game
        sem3 = threading.Semaphore()
        if not quiz_id_queue.empty():
            # lock the semaphore
            sem3.acquire()
            quiz_id = quiz_id_queue.get()
            # release the semaphore
            sem3.release()

            game_thread = threading.Thread(target=handle, args=(client_soc_obj, quiz_id))
            game_thread.start()

            # Add the game thread to the queue
            threads_queue.put(game_thread)


if __name__ == "__main__":
    # Connection Data
    host = '127.0.0.1'
    port = 8009
    FORMAT = 'utf-8'  # Define the encoding format of messages from client-server
    # Starting Server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    # create semaphore for the threads
    sem = threading.Semaphore()

    # create global data base object
    quiz_db = QuizDataBase()
    isAccepted = False
    # queue for the quiz_id
    quiz_id_queue = queue.Queue()
    # queue for threads
    threads_queue = queue.Queue()
    # start the server
    start_server()
