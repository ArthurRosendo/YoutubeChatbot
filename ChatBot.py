import pickle
import os
import string
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import regex
import grapheme
import Person


class ChatBot:

    # Tags and Ids for Selenium
    message_tag = "yt-live-chat-text-message-renderer"
    chatframe_id = "chatframe"
    video_player_tag = "div"
    video_player_id = "movie_player"

    def __init__(self, _url):
        self.evaluate_livestream_url(_url)

        self.url = _url
        self.is_VOD = True  # Mostly for testing purpose
        self.autoplay_is_on = False  # Change this to True if autoplay is on
        self.bot_running = True
        self.messageHistory = list()

        self.disallowed_terms = set()
        self.regex_patterns = set()

        self.whitelist_path = "whitelist.p"
        self.blacklist_path = "blacklist.p"

        # Whitelist loading
        if os.path.isfile(self.whitelist_path):
            whitelist_file = open(self.whitelist_path, "rb")
            self.whitelisted_people: set[Person] = set(pickle.load(whitelist_file))
            whitelist_file.close()
        else:
            self.whitelisted_people: set[Person] = set()
            whitelist_file = open(self.whitelist_path, "x")
            self.save_to_file(self.whitelisted_people, self.whitelist_path)
        # Blacklist loading
        if os.path.isfile(self.blacklist_path):
            blacklist_file = open(self.blacklist_path,"rb")
            self.blacklisted_people: set[Person] = set(pickle.load(blacklist_file))
            blacklist_file.close()
        else:
            self.blacklisted_people: set[Person] = set()
            whitelist_file = open(self.blacklist_path, "x")
            self.save_to_file(self.blacklisted_people, self.blacklist_path)

        self.driver = None

        self.setup()
        # self.run()

    def evaluate_livestream_url(self, _url):
        if self.is_url(_url):
            if regex.search(r"youtube\.com\/watch\?v=.+$", _url) is None:
                raise Exception("Invalid URL")
        else:
            raise Exception("Not a URL")

    def setup(self):
        self.selenium_setup()

    def selenium_setup(self):
        # TODO: Consider locating elements via XPATH
        self.driver = None
        # soup = BeautifulSoup(urlopen(self.url), 'html.parser')
        options = Options()
        # options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.url)

        # === VIDEO PLAYER ===

        video_player_element = self.driver.find_element(By.ID, self.video_player_id)
        # Keep waiting while the video is not fully loaded
        while True:
            print("Waiting for video player...")
            try:
                WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable(video_player_element))
                break
            except:
                pass

        # If it is a VOD clicks on video player automatically to start the chat if autoplay is off
        if self.is_VOD is True:
            if self.autoplay_is_on is False:
                video_player_element.click()

        # === CHAT FRAME ===
        while True:
            print("Waiting for chat frame...")
            try:
                chatframe_element = self.driver.find_element(By.ID, self.chatframe_id)
                WebDriverWait(self.driver, 1).until(EC.visibility_of(chatframe_element))
                self.driver.switch_to.frame(chatframe_element)
                break
            except:
                pass

        # Wait until a message shows up
        while True:
            print("Waiting for chat message...")
            try:
                WebDriverWait(self.driver, 1).until(EC.visibility_of(self.driver.find_element(By.TAG_NAME, self.message_tag)))
                break
            except:
                pass
        print("Found message(s)")

        # Changing to live chat replay
        button = self.driver.find_element(By.ID, "view-selector")
        button.click()
        while True:
            print("Waiting for live chat replay button...")
            try:
                aux = button.find_elements(By.TAG_NAME, "a")[1]
                WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable(aux))
                aux.click()
                break
            except:
                pass

    def run(self):
        # TODO: add a way to stop the bot
        while self.bot_running is True:
            self.selenium_run()

    def selenium_run(self):
        messages_elements = self.driver.find_elements(By.TAG_NAME, self.message_tag)

        for message_element in messages_elements:
            message_content = message_element.find_element(By.ID, "content")
            print("-------------------")
            print(message_content.text)
            print("-------------------")

            # TODO: store messages on a file or db

            # TODO: retrieve the actual text message from the message element

            # TODO: evaluate if message or messenger:
            # Is posted too much by the same user (spam)
            # Is posted too much by multiple users (dynamic copypasta detection)
            # Uses spammy characters? (Symbol protection)
            # Disguised link (eg.: "example .xyz")
            # Synonym match
            # Shared channel-blacklist

            # TODO: respond to preset commands from moderators and the streamer
            time.sleep(0.1)


    def selenium_send_message(self, _message):
        raise NotImplementedError
        # TODO: Select chatbox
        # TODO: Prepare message
        # TODO: Select and click submit button

    def whitelist(self, _person):
        if not self.evaluate_whitelist(_person):
            self.whitelisted_people.add(_person)
            self.save_to_file(self.whitelisted_people, self.whitelist_path)

    def remove_from_whitelist(self, _person):
        if self.evaluate_whitelist(_person):
            self.whitelisted_people.discard(_person)
            self.save_to_file(self.whitelisted_people, self.whitelist_path)

    def evaluate_whitelist(self, _person):
        for i in self.whitelisted_people:
            if i.same_person(_person):
                return True
        return False

    def blacklist(self, _person):
        if not self.evaluate_blacklist(_person):
            self.blacklisted_people.add(_person)
            self.save_to_file(self.blacklisted_people, self.blacklist_path)

    def remove_from_blacklist(self, _person):
        if self.evaluate_blacklist(_person):
            self.blacklisted_people.discard(_person)
            self.save_to_file(self.blacklisted_people, self.whitelist_path)

    def evaluate_blacklist(self, _person):
        for i in self.blacklisted_people:
            if i.same_person(_person):
                return True
        return False

    def save_to_file(self, _set, _path):
        file = open(_path,"wb")
        pickle.dump(_set, file)
        file.close()

    def add_message(self, _message):
        message_already_added = False
        # TODO: replace list with Deque and remove the reversed()?
        for i in reversed(self.messageHistory):
            if i.sameMessage(_message):
                message_already_added = True
                break
        if not message_already_added:
            self.messageHistory.append(_message)

    def disallow_term(self, _term):
        if _term:
            self.disallowed_terms.add(_term)

    def allow_term(self, _term):
        if _term:
            self.disallowed_terms.discard(_term)

    def evaluate_term(self, _message):
        flag = regex.I #TODO: If it should be case-sensitive than it is probably better let the user determine it

        for term in self.disallowed_terms:
            if regex.search(r"\Q"+term+r"\E", _message, flag):
                return True
        return False

    def add_pattern(self, _pattern: string):
        if _pattern:
            _pattern = _pattern.encode('unicode_escape')
            try:
                regex.compile(_pattern)
                self.regex_patterns.add(_pattern)
            except regex.error:
                pass #TODO: Maybe should just let it cause regex.error or return False

    def remove_pattern(self, _pattern):
        if _pattern:
            self.regex_patterns.discard(_pattern)

    def evaluate_regex(self, _message):
        for pattern in self.regex_patterns:
            if regex.search(pattern, _message):
                return True
        return False

    @staticmethod
    def is_url(_message):
        pattern = r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-zA-Z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&\/=]*)'
        return regex.search(pattern, _message) is not None

    # If it is a URL with spaces in some places
    # TODO: FIX ME: this currently is matching any word followed by a period and a another text (eg.: "Hello. How are you") is considered a link
    @staticmethod
    def is_sneaky_url(self, _message):
        raise NotImplementedError
        pattern = r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}[ ]*\.[ ]*[a-zA-Z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&\/=]*)"
        return regex.search(pattern, _message)

    # TODO: Do more intensive tests
    @staticmethod
    def evaluate_diacritic_spam(_message):
        if len(_message) == 0:
            return False

        if len(_message) > len(list(grapheme.graphemes(_message))) * 5:
            return True
        else:
            return False
