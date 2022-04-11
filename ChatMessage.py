from __future__ import annotations
import Person


class ChatMessage:

    # TODO: Consider adding message ID if Youtube has it available
    def __init__(self, _id:str, _timestamp, _message:str, _person: Person):
        self.id = _id
        self.timestamp = _timestamp
        self.message = _message
        self.person = _person

    """ Checks if the message is the same """
    def same_message(self, _other_message: ChatMessage) -> bool:
        return _other_message.timestamp == self.timestamp and _other_message.message == self.message and _other_message.person == self.person
