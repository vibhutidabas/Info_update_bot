from multiply_ai_coding_task.chat import (
    ConversationState,
    Message,
    Sender,
    chat_response,
)

def demo():
    """A simple demo script to show the conversation between a user and AI"""
    print("--Starting chat demo, please enter your request to get started.--")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    state = ConversationState()
    while True:
        user_message = input("Vibhu: ")

        if user_message.strip().lower() == "exit":
            break

        state.messages.append(Message(text=user_message, sender=Sender.USER))
        state = chat_response(state)

        for message in state.new_messages:
            print(f"Gemi: {message.text}")
            state.messages.append(message)

    print("\n--Ending conversation--")
    print("\n Information collected about the user:\n")
    print(state.extracted_information)

# def demo():
#     """A simple demo script to show the conversation between a user and AI"""
#     print("--Starting chat demo, please enter your request to get started.--")

#     state = ConversationState()

#     while True:
#         user_message = input("Vibhu: ")
#         state.messages.append(Message(text=user_message, sender=Sender.USER))

#         state = chat_response(state)

#         while len(state.new_messages) > 0:
#             message = state.new_messages.pop(0)
#             print(f"AI: {message.text}")
#             state.messages.append(message)

#         if state.finished:
#             print("--Ending conversation--")
#             print("Information collected about the user:", state.extracted_information)
#             break
