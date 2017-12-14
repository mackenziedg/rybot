from collections import defaultdict
import os
from random import choice
import time
from slackclient import SlackClient
from doc_matching import DocumentFinder
import praise


class Rybot:

    def __init__(self):
        self.bot_id = os.environ.get('BOT_ID')
        self.slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
        assert self.bot_id is not None
        assert self.slack_bot_token is not None

        self.at_bot = '<@' + self.bot_id + '>'
        self.slack_client = SlackClient(self.slack_bot_token)
        print("Rybot connected!")

        # Must come after the command definitions
        self.commands = {'docs': self.get_docs,
                         'fightme': self.get_donger,
                         'praise': self.praise,
                         'so': self.get_stackoverflow}

        print("Setting up stackoverflow searching")
        self.doc_finder = DocumentFinder()
        print("Done!")
        self.read_websocket_delay = 1  # 1 second delay between reading from firehose

    def start(self):
        """Connect to the Slack channel and begin reading posts.

        Raises
        ------
        ValueError
            If the bot cannot connect to the Slack channel for some reason
        """
        if self.slack_client.rtm_connect():
            print("Rybot connected and running!")
            while True:
                userid, command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                if command and channel:
                    self.handle_command(userid, command, channel)
                time.sleep(self.read_websocket_delay)
        else:
            raise ValueError("Connection failed. Invalid Slack token or bot ID?")

    def handle_command(self, userid, command, channel):
        """Parses input from `self.parse_slack_output()` and acts on the input, if valid.

        Parameters
        ----------
        userid : string
            User id of the user who sent the message being parsed
        command : string
            Command directed at @rybot, not including the '@rybot' tag
        channel : string
            Channel id where rybot is being questioned
        """
        response = None
        username = self.userid_to_name(userid)
        tokens = command.split(' ')
        command = tokens[0]

        # Pretends to be typing while we wait to respond

        self.slack_client.server.send_to_websocket({"id": 1, "type": "typing", "channel": channel})
        if command in self.commands.keys():
            args = ' '.join(tokens[1:]).lower()
            response = self.commands[command](username, args)
        if response is None:
            response = 'Try one of {}.'.format(self.commands.keys())
        self.slack_client.api_call("chat.postMessage", channel=channel,
                            text=response, as_user=True)

    def parse_slack_output(self, slack_rtm_output):
        """Parses messags directed at @rybot.

        Parameters
        ----------
        slack_rtm_output : string
            String of the message directed at @rybot

        Returns
        -------
        message_info : tuple
            A tuple of the user, text, and channel associated with a message. Defaults to `None`
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and self.at_bot in output['text']:
                    return output['user'], output['text'].split(self.at_bot)[1].strip(), output['channel']
        return None, None, None

    def userid_to_name(self, userid):
        """Converts a Slack user id into the first name associated with that id.

        Parameters
        -----------
        userid : string
            The Slack user id to be converted

        Returns
        -------
        username : string
            The associated username, if exists. Otherwise returns `None`
        """
        response = self.slack_client.api_call("users.info", user=userid)
        return response.get('user', None).get('profile', None).get('first_name', None)

    def praise(self, name, args):
        """A wrapper for the praise() function which adds the user's listed first name to the praise.

        Parameters
        ----------
        name : string
            User name requesting the praise
        args : string
            Any arguments passed to self.praise() (Does not do anything currently)

        Returns
        -------
        praise : string
            A message prasing the user
        """
        message = choice([
            'You are ${{adjective}}, {0}.',
            '${{Exclamation}} {0}! You\'re ${{adjective}}!',
            '{0}, you are doing ${{adjective}}!'
        ])
        return praise.praise(message.format(name))

    def get_docs(self, name, args):
        """Returns a link to documentation for a specified package or software.

        Parameters
        ----------
        name : string
            User name requesting documentation
        args : string
            Name of software for which documentation is requested

        Returns
        -------
        link : string
            URL of the documentation requested, or a message indicating the error, if any
        """
        docs_undef_error = 'Sorry {0}, I don\'t have documentation for that package. Try `@rybot docs list` to list available documentation.'.format(name)
        docs_dict = defaultdict(lambda: docs_undef_error)
        docs_dict.update({
            'numpy': 'https://docs.scipy.org/doc/numpy/',
            'scipy': 'https://docs.scipy.org/doc/scipy/reference/',
            'pandas': 'https://pandas.pydata.org/pandas-docs/stable/api.html',
            'mongo': 'https://docs.mongodb.com/',
            'postgres': 'https://www.postgresql.org/docs/'
            })
        if args == 'list':
            return '\n'.join(sorted([d for d in docs_dict.keys()]))
        else:
            success_msg = 'Here you go {0}: {1}'.format(name, docs_dict[args])
            return success_msg

    def get_donger(self, name, args):
        """Returns a fightin' donger at the users challenge.

        Parameters
        ----------
        name : string
            User name requesting a fight
        args : string
            Any additional arguments (not used)

        Returns
        -------
        donger : string
            A unicode donger, selected at random
        """
        dongers = [
            '(ᕗ ͠°  ਊ ͠° )ᕗ',
            'ᕙ(° ͜ಠ ͜ʖ ͜ಠ°)ᓄ',
            '(́ง◉◞౪◟◉‵)ง',
            '(ง ° ͜ ʖ °)ง',
            '༼ง=ಠ益ಠ=༽ง'
        ]
        return choice(dongers)

    def get_stackoverflow(self, name, args):
        """Returns a url and title for the most similar StackOverflow question
        Parameters
        ----------
        name : string
            User name requesting a SO search
        args : string
            Any additional arguments

        Returns
        -------
        url -- The url of the closest question
        string -- The title of the closest question
        """
        return self.doc_finder.get_closest(args)

if __name__ == '__main__':
    ryb = Rybot()
    ryb.start()
