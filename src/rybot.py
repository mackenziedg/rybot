from collections import defaultdict
import os
import time
from slackclient import SlackClient
import praise


class Rybot:

    def __init__(self):
        '''
        Initialize the neccessary (environment) variables.
        '''
        self.bot_id = os.environ.get('BOT_ID')
        self.at_bot = '<@' + self.bot_id + '>'
        self.slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
        self.slack_client = SlackClient(self.slack_bot_token)
        self.docs_dict = {
            'numpy': 'https://docs.scipy.org/doc/numpy-1.13.0/index.html',
            'scipy': 'https://docs.scipy.org/doc/scipy/reference/',
            'pandas': 'https://pandas.pydata.org/pandas-docs/stable/api.html',
            'mongo': 'https://docs.mongodb.com/',
            'postgres': 'https://www.postgresql.org/docs/'
            }
        self.docs_undef_error = 'Sorry, I don\'t have documentation for that. Try one of {}'.format([k for k in self.docs_dict.keys()])
        self.docs = lambda x: self.docs_dict[x] if x in self.docs_dict.keys() else self.docs_undef_error
        self.fightme = lambda _: 'http://i.imgur.com/Skqd8Rf.jpg'
        self.praise = lambda _: praise.praise() 

        # Must come after the command definitions
        self.commands = {'docs': self.docs, 'fightme': self.fightme, 'praise': self.praise}
        self.read_websocket_delay = 1  # 1 second delay between reading from firehose

    def start(self):
        '''
        Connect to the Slack channel and begin reading posts.
        '''
        if self.slack_client.rtm_connect():
            print("Rybot connected and running!")
            while True:
                command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                if command and channel:
                    self.handle_command(command, channel)
                time.sleep(self.read_websocket_delay)
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

    def handle_command(self, command, channel):
        '''
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        '''
        response = None
        tokens = command.split(' ')
        command = tokens[0]
        if command in self.commands.keys():    
            args = ' '.join(tokens[1:]).lower()
            response = self.commands[command](args)
        if response is None:
            response = 'Try one of {}.'.format(self.commands.keys())
        self.slack_client.api_call("chat.postMessage", channel=channel,
                            text=response, as_user=True)

    def parse_slack_output(self, slack_rtm_output):
        '''
            the slack real time messaging api is an events firehose.
            this parsing function returns none unless a message is
            directed at the bot, based on its id.
        '''
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and self.at_bot in output['text']:
                    return output['text'].split(self.at_bot)[1].strip().lower(), output['channel']
        return None, None


if __name__ == '__main__':
    ryb = Rybot()
    ryb.start()
