
from llm import talk, getMemory

while True:
    result = talk(input(">> "))

    # print("++++++++++++++++++++++v")
    # print(result)
    # # 
    # print("++++++++++++++++++++++^")
    # print(result['question'] + "\n")
    # print(result['chat_history'])
    # print(type(result['chat_history']))
    # print("+++++++++++ get content vvv +++++++++++^")
    # print(result['chat_history'][1])
    print(">> Print: \n")
    print(result)
    print("\n")
    # print(getMemory())
