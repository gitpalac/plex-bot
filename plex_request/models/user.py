class UserMessage:
    def __init__(self, message):
        self.id = message['id']
        self.type = message['type']
        self.timestamp = message['timestamp']
        self.timestampEdited = message['timestampEdited']
        self.isPinned = message['isPinned']
        self.content = message['content']
        self.author_id = message['author']['id']
        self.author_name = message['author']['name']
        self.hasUrl = self.content.find('https://') != -1

    def append_content(self, content):
        self.content = self.content + ' ' + content