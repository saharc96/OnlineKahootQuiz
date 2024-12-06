import socket
import threading
import time
import numpy as np


class QuizDataBase:
    # constructor
    def __init__(self):
        self.quizes = []
        self.quiz_id = 0
        self.clients = []
        self.password = ''

        # for the quizes:
        self.questions = []
        self.answers = []
        self.correct_answers = []
        self.category = ''

        # for the waiting room:
        self.current_num_of_participants = 0
        self.excepted_num_of_participants = 0

        # number of players finished the quiz
        self.num_of_finished_players = 0


    def update_password(self, password):
        """
        Update the password of the quiz
        :param password:
        :return:
        """
        self.password = password

    def return_current_id(self):
        return self.quiz_id

    def set_num_of_participants(self, num_of_participants):
        """
        Set the number of participants
        :param num_of_participants:
        :return:
        """
        self.excepted_num_of_participants = num_of_participants
        self.current_num_of_participants = 1

    # for the clients:
    def add_client(self, name, client):
        """
        Add a new client to the database
        :param client:
        :param name:
        :return:
        """
        # third element is the score of the client
        self.clients.append((name, client, 0))

    def remove_client(self, name, client):
        """
        Remove a client from the database
        :param name:
        :param client:
        :return:
        """
        for nam, cli in self.clients:
            if cli == client and nam == name:
                self.clients.remove((nam, cli))
                return

    def add_quiz(self, file_path):
        """
        Add a new quiz to the database
        :param file_path: the path of the quiz file
        :return:
        """
        self.category = file_path[:-4]
        # load the quiz from txt file
        with open(file_path, 'r') as file:
            # get the category of the quiz from the first line
            questions_answers = []
            # get the questions and answers from the file using a loop
            for line in file:
                # split the line to question and answer
                if line[0] == 'Q':
                    question = line[2:-1]
                    self.questions.append(question)

                elif line[0] == 'A':
                    answer = line[2:-1]
                    questions_answers.append(answer)
                    if len(questions_answers) == 4:
                        self.answers.append(questions_answers)
                        questions_answers = []
                elif line[0:2] == 'CA':
                    correct_answer = line[3:-1]
                    self.correct_answers.append(correct_answer)

                elif line.strip() in 'END_OF_QUIZ':
                    # use dictionary to store the quiz
                    new_quiz_dic = {'QuizId': self.quiz_id, 'Password': self.password,
                                    'ExcpectedNumParticipents': self.excepted_num_of_participants,
                                    'CurrentNumParticipents': self.current_num_of_participants,
                                    'Category': self.category, 'Clients': self.clients,
                                    'Questions': self.questions, 'Answers': self.answers,
                                    'CorrectAnswers': self.correct_answers,
                                    'NumOfFinishedPlayers': self.num_of_finished_players
                                    }

                    self.quizes.append(new_quiz_dic)
                    # reset the questions and answers lists
                    self.questions = []
                    self.answers = []
                    self.correct_answers = []
                    self.clinets = []
                    self.quiz_id += 1
                    self.password = ''
                    self.current_num_of_participants = 0
                    self.excepted_num_of_participants = 0
                    self.num_of_finished_players = 0
                    break

    def score_quiz(self, client, answer, quiz_id, time_to_answer):
        """"
        Score the quiz given an answer
        :param client: the client object
        :param answer : the answer of the client
        :param quiz_id: the id of the quiz
        :param time_to_answer: the time the client took to answer
        :return: True if the answer is correct, False otherwise
        """
        # get the index of the client
        index = -1
        for client_t in self.quizes[quiz_id]["Clients"]:
            if client_t[1] == client:
                index = self.quizes[quiz_id]["Clients"].index(client_t)
                break

        # get the answer from the list
        correct_answer = self.quizes[quiz_id]["CorrectAnswers"][index]
        print('answer of client:', answer, ' correct answer:', correct_answer)
        print('types of correct answer:', type(correct_answer), ' type of answer:', type(answer))
        # check if the answer is correct
        if int(answer) == int(correct_answer):
            # calc random bonus according to the time it took to answer
            bonus = np.random.randint(1, 4) * (25 - time_to_answer)
            # add 1 to the score
            # create new tuple with updated score and then insert it insted of the current one
            self.quizes[quiz_id]["Clients"][index] = (self.quizes[quiz_id]["Clients"][index][0],
                                                      self.quizes[quiz_id]["Clients"][index][1],
                                                      self.quizes[quiz_id]["Clients"][index][2] + 1 + bonus)
            return True
        return False




# quiz_db = QuizDataBase()
#
# # load a quiz
# #quiz_db.add_quiz('Physics.txt')
# #quiz_db.add_quiz('Capital_Cities.txt')
# #quiz_db.add_quiz('Math.txt')
#
# print(quiz_db.quizes)
