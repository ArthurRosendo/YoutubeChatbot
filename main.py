from ChatBot import ChatBot
from Person import Person

link = open("testlink.txt","r")
chatbot = ChatBot(link.read())