from __future__ import annotations
import string


class Person:

    def __init__(self, _channel_id, _channel_name: string = None):
        self.channelId = _channel_id
        self.alias: set[string] = set()
        if _channel_name:
            self.alias.add(_channel_name)

    def add_alias(self, _other_person: Person):
        if self.same_person(_other_person):
            self.alias.update(_other_person.alias)

    def same_person(self, _other_person: Person):
        return _other_person.channelId == self.channelId
