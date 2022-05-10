from __future__ import annotations
import Person


class ChatMessage:

    # TODO: Consider adding message ID if Youtube has it available
    def __init__(self, _id:str, _timestamp, _message:str):
        self.id = _id
        self.timestamp = _timestamp
        self.message = _message
        #self.person = _person #TODO: Add?

    """ Checks if the message is the same """
    def same_message(self, _other_message: ChatMessage) -> bool:
        return self.id == _other_message.id
