from collections import defaultdict
import os
from random import choice
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

        # Must come after the command definitions
        self.commands = {'docs': self.get_docs, 'fightme': self.get_donger, 'praise': self.praise}
        self.read_websocket_delay = 1  # 1 second delay between reading from firehose

    def start(self):
        '''
        Connect to the Slack channel and begin reading posts.
        '''
        if self.slack_client.rtm_connect():
            print("Rybot connected and running!")
            while True:
                userid, command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                if command and channel:
                    self.handle_command(userid, command, channel)
                time.sleep(self.read_websocket_delay)
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

    def handle_command(self, userid, command, channel):
        '''
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        '''
        response = None
        username = self.userid_to_name(userid)
        tokens = command.split(' ')
        command = tokens[0]
        if command in self.commands.keys():    
            args = ' '.join(tokens[1:]).lower()
            response = self.commands[command](username, args)
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
                    return output['user'], output['text'].split(self.at_bot)[1].strip(), output['channel']
        return None, None, None

    def userid_to_name(self, userid):
        response = self.slack_client.api_call("users.info", user=userid)
        return response['user']['profile']['first_name']
        
    def praise(self, name, args):
        '''
        A wrapper for the praise() function which adds the user's listed first name to the praise.
        '''
        message = choice([
            'You are ${{adjective}}, {0}.',
            '${{Exclamation}} {0}! You\'re ${{adjective}}!',
            '{0}, you are doing ${{adjective}}!'
        ])
        return praise.praise(message.format(name))

    def get_docs(self, name, args):
        docs_undef_error = 'Sorry, I don\'t have documentation for that.'
        docs_dict = defaultdict(lambda: docs_undef_error)
        docs_dict.update({
            'numpy': 'https://docs.scipy.org/doc/numpy/',
            'scipy': 'https://docs.scipy.org/doc/scipy/reference/',
            'pandas': 'https://pandas.pydata.org/pandas-docs/stable/api.html',
            'mongo': 'https://docs.mongodb.com/',
            'postgres': 'https://www.postgresql.org/docs/'
            })
        return docs_dict[args]

    def get_donger(self, name, args):
        dongers = [
            '(ᕗ ͠°  ਊ ͠° )ᕗ',
            'ᕙ(° ͜ಠ ͜ʖ ͜ಠ°)ᓄ',
            '(́ง◉◞౪◟◉‵)ง',
            '(ง ° ͜ ʖ °)ง',
            '༼ง=ಠ益ಠ=༽ง'
        ]
        return choice(dongers)
    

if __name__ == '__main__':
    ryb = Rybot()
    ryb.start()
