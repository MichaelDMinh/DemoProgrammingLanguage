print("DEMO VERSION 1")
print("Made by Michael Dovidson Minh")
print("Type !help for a list of commands.")

import time

#PRINT OPERATION

while True:
    text = input(">>> ")
    print(text)

#MATH OPERATIONS

    if text.startswith("!calc "):
        text = text[5:]
        result = eval(text)
        print(result)
    
#KILL PROGRAM OPERATION

    if text == "!exit":
        print("Exiting program...")
        time.sleep(1)
        exit()

#HELP OPERATION
    if text == "!help":
        print("Available commands:")
        print("!calc <expression> - Calculate the mathematical expression.")
        print("!exit - Exit the program.")
        print("!help - Show this help message.")