import os
import time
from slackclient import SlackClient


BOT_ID = os.environ.get('BOT_ID')
AT_BOT = '<@' + BOT_ID + '>'
NUMPY_DOCS_URL = ""

def handle_command(command, channel):
    '''
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    '''
    commands = ['docs', 'fightme']
    response = 'Try one of {}.'.format(commands)

    tokens = command.split(' ')
    command = tokens[0]
    if command in commands:    
        if command == 'docs':
            docs_for = ' '.join(tokens[1:]).lower()
            print(docs_for)
            docs_dict = {
                'numpy': 'https://docs.scipy.org/doc/numpy-1.13.0/index.html',
                'scipy': 'https://docs.scipy.org/doc/scipy/reference/',
                'pandas': 'https://pandas.pydata.org/pandas-docs/stable/api.html',
                'mongo': 'https://docs.mongodb.com/',
                'postgres': 'https://www.postgresql.org/docs/'
            }
            if docs_for in docs_dict.keys():
                response = 'RTFM: {}'.format(docs_dict[docs_for])
            else:
                response = 'Sorry, that library is currently not supported.'
        if command == 'fightme':
            response = 'http://i.imgur.com/Skqd8Rf.jpg'

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    '''
        the slack real time messaging api is an events firehose.
        this parsing function returns none unless a message is
        directed at the bot, based on its id.
    '''
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                    output['channel']
    return None, None


if __name__ == '__main__':
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("rybot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
