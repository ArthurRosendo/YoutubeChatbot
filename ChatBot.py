import datetime
import pickle
import os
import string
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import time
import regex
import grapheme
import Person
from ChatMessage import ChatMessage


class ChatBot:
    # Tags and Ids for Selenium
    MESSAGE_TAG = "yt-live-chat-text-message-renderer"
    CHATFRAME_ID = "chatframe"
    VIDEO_PLAYER_TAG = "div"
    VIDEO_PLAYER_ID = "movie_player"
    CHATBOX_ID = "input"

    def __init__(self, _url):
        self.evaluate_livestream_url(_url) # Check if URL is valid
        self.url = _url
        self.is_VOD = True  # For testing purposes - distinction may be removed later since a bot in a recorded stream doesn't make a lot of sense
        self.autoplay_is_on = False  # Change this to True if autoplay on YT is on
        self.bot_running = True
        self.messageHistory = list[ChatMessage]()
        self.last_execution = None
        self.update_last_execution()

        self.disallowed_terms = set()
        self.regex_patterns = set()

        # region === People blacklist and whitelist ===
        self.whitelist_path = "whitelist.p"
        self.blacklist_path = "blacklist.p"
        #region Whitelist loading
        if os.path.isfile(self.whitelist_path):
            #Read whitelist file
            whitelist_file = open(self.whitelist_path, "rb")
            self.whitelisted_people: set[Person] = set(pickle.load(whitelist_file))
            whitelist_file.close()
        else:
            #Create whitelist file
            self.whitelisted_people: set[Person] = set()
            whitelist_file = open(self.whitelist_path, "x")
            whitelist_file.close()
            self.save_to_file(self.whitelisted_people, self.whitelist_path)
        #endregion

        #region Blacklist loading
        if os.path.isfile(self.blacklist_path):
            #Read blacklist file
            blacklist_file = open(self.blacklist_path, "rb")
            self.blacklisted_people: set[Person] = set(pickle.load(blacklist_file))
            blacklist_file.close()
        else:
            #Create blacklist file
            self.blacklisted_people: set[Person] = set()
            blacklisted_file = open(self.blacklist_path, "x")
            blacklisted_file.close()
            self.save_to_file(self.blacklisted_people, self.blacklist_path)
        #endregion
        #endregion

        self.driver = None
        self.setup()
        #self.run()

    @staticmethod
    def evaluate_livestream_url(_url):
        if ChatBot.is_url(_url):
            if regex.search(r"youtube\.com\/watch\?v=.+$", _url) is None:
                raise Exception("Invalid URL - provided url is not a livestream/video")
        else:
            raise Exception("Not an URL")

    def setup(self):
        # TODO ?: Replace locating elements with via XPATH?
        self.driver = None
        # soup = BeautifulSoup(urlopen(self.url), 'html.parser')
        options = Options()
        # options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.url)

        # === VIDEO PLAYER ===

        video_player_element = self.driver.find_element(By.ID, self.VIDEO_PLAYER_ID)
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
                chatframe_element = self.driver.find_element(By.ID, self.CHATFRAME_ID)
                WebDriverWait(self.driver, 1).until(EC.visibility_of(chatframe_element))
                self.driver.switch_to.frame(chatframe_element)
                break
            except:
                pass

        # Wait until a message shows up
        while True:
            print("Waiting for chat message...")
            try:
                WebDriverWait(self.driver, 1).until(
                    EC.visibility_of(self.driver.find_element(By.TAG_NAME, self.MESSAGE_TAG)))
                break
            except:
                pass
        print("Found message(s)")

        # Changing to live chat replay (this is for both streams AND vods)
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

    def add_message_to_history(self, _msg:ChatMessage):
        for msg in self.messageHistory:
            if msg.same_message(_msg):
                return
        self.messageHistory.append(_msg)

    def update_last_execution(self):
        self.last_execution = datetime.now().strftime("%H:%M:%S")

    def run(self):
        while self.bot_running:
            messages_elements = self.driver.find_elements(By.TAG_NAME, self.MESSAGE_TAG)

            for message_element in messages_elements:
                msg_id = message_element.getAttribute("id")
                message_content = message_element.find_element(By.ID, "content")
                message_timestamp = message_content.find_element(By.ID, "timestamp").getText()
                message_text = message_content.find_element(By.ID, "message").getText()
                #TODO: get who sent the message? How to obtain channel id?
                self.add_message_to_history( ChatMessage(msg_id, message_timestamp, message_text) )

                # TODO: store messages on a file or db
                # TODO: retrieve the actual text message from the message element
                # TODO: evaluate if message or messenger:
                # Is posted too much by the same user (spam)
                # Is posted too much by multiple users (dynamic copypasta detection)
                # Uses spammy characters? (Symbol protection)
                # Disguised link (eg.: "example .xyz")
                # Synonym match
                # Shared channel-blacklist

                #TODO: check if the user is the streamer (or moderator) that sent the message or remove this functionality entirely
                if message_content.text == "!quit":
                    break

                self.update_last_execution()
                time.sleep(0.2)

    # TODO: test
    def send_message(self, _message: str):
        if not self.is_VOD:
            if not _message:
                return

            chatframe_element = self.driver.find_element(By.ID, self.CHATFRAME_ID)
            print("send_message: Waiting for chatframe")
            WebDriverWait(self.driver, 1).until(EC.visibility_of(chatframe_element))
            self.driver.switch_to.frame(chatframe_element)

            chatbox_element = self.driver.find_element(By.ID, self.CHATBOX_ID)
            print("send_message: Waiting for chatbox")
            WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable(chatbox_element))
            chatbox_element.click()
            #Clear chatbox before sending message
            chatbox_element.sendKeys(Keys.CONTROL + "a")
            chatbox_element.sendKeys(Keys.DELETE)
            #Send
            chatbox_element.sendKeys(_message)

            chat_submit_button_element = self.driver.find_element(By.ID, "button")
            print("send_message: Waiting for submit button")
            WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable(chat_submit_button_element))
            print(chat_submit_button_element)
            #chat_submit_button_element.click()  # TODO: Removed for testing sake, please uncomment this

    # WHITELIST
    def whitelist(self, _person:Person):
        if not self.evaluate_whitelist(_person):
            self.whitelisted_people.add(_person)
            self.save_to_file(self.whitelisted_people, self.whitelist_path)

    def remove_from_whitelist(self, _person:Person):
        if self.evaluate_whitelist(_person):
            self.whitelisted_people.discard(_person)
            self.save_to_file(self.whitelisted_people, self.whitelist_path)

    def evaluate_whitelist(self, _person:Person):
        for i in self.whitelisted_people:
            if i.same_person(_person):
                return True
        return False

    # BLACKLIST
    def blacklist(self, _person: Person):
        if not self.evaluate_blacklist(_person):
            self.blacklisted_people.add(_person)
            self.save_to_file(self.blacklisted_people, self.blacklist_path)

    def remove_from_blacklist(self, _person: Person):
        if self.evaluate_blacklist(_person):
            self.blacklisted_people.discard(_person)
            self.save_to_file(self.blacklisted_people, self.whitelist_path)

    def evaluate_blacklist(self, _person: Person):
        for i in self.blacklisted_people:
            if i.same_person(_person):
                return True
        return False

    def add_message(self, _message):
        message_already_added = False
        # TODO: replace list with Deque and remove the reversed()?
        for i in reversed(self.messageHistory):
            if i.same_message(_message):
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
        flag = regex.I  # TODO: If it should be case-sensitive than it is probably better let the user determine it

        for term in self.disallowed_terms:
            if regex.search(r"\Q" + term + r"\E", _message, flag):
                return True
        return False

    def add_pattern(self, _pattern: string):
        if _pattern:
            _pattern = _pattern.encode('unicode_escape')
            try:
                regex.compile(_pattern)
                self.regex_patterns.add(_pattern)
            except regex.error:
                pass  # TODO: Maybe should just let it cause regex.error or return False

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

    # TODO: Do more intensive tests
    @staticmethod
    def evaluate_diacritic_spam(_message):
        if len(_message) == 0:
            return False

        if len(_message) > len(list(grapheme.graphemes(_message))) * 5:
            return True
        else:
            return False

    @staticmethod
    def save_to_file(_set, _path):
        file = open(_path, "wb")
        pickle.dump(_set, file)
        file.close()
