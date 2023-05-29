import time
import slack_sdk
from slack_sdk.errors import SlackApiError

class Conversation:

    def __init__(self):
        self.bot_response_messages = []
        self.last_user_message = {}
        self.history = []

        oauth_token = ""
        self.claude_id = ""
        self.channel_id = ""
        self.sleep_constant = 0.5
        self.client = slack_sdk.WebClient(token=oauth_token)

    # 向Slack频道发送消息
    def send_message(self, message):
        try:
            self.client.chat_postMessage(channel=self.channel_id, text=message)
        except SlackApiError as e:
            print(f"error:{e.response['error']}")
        except Exception as e:
            print(f"unknown:{e}")
            print("retry...")
            try_count = 0
            while try_count < 3:
                try:
                    self.client.chat_postMessage(channel=self.channel_id, text=message)
                    break
                except Exception as e:
                    print(f"retry error:{e}")
                    try_count += 1
            print("tried three times, exit now")
            exit()

        self.history.append(message)

    def get_bot_response_from_history(self, not_just_print=False):
        while True:

            # response = self.client.conversations_history(channel=self.channel_id, oldest=self.last_user_message["ts"])
            response = self.client.conversations_history(channel=self.channel_id,
                                                         #oldest=self.last_user_message["ts"],
                                                         #inclusive=True,
                                                         limit=1)
            messages = response["messages"]

            self.bot_response_messages = [m for m in messages if m["user"] == self.claude_id]
            if len(self.bot_response_messages) > 0:
                if '_Typing…_' not in self.bot_response_messages[-1]['text']:
                    break
            time.sleep(self.sleep_constant)
        print("机器人：", self.bot_response_messages[-1]['text'])
        if not_just_print:
            return self.bot_response_messages[-1]['text']

    def read_input(self):
        # 先获取输入
        message = input("You:")
        self.get_input(message)

    def get_input(self, message):
        print("You: ", message)
        # 发送消息
        self.send_message(message)
        # 记录输入
        self.last_user_message = {
            "ts": str(time.time()),
            "text": message
        }

# conversation = Conversation()
# while True:
#     conversation.read_input()
#     conversation.get_bot_response_from_history()
