"""An IMDbot built on aSlack and IMDbPY."""

from collections import OrderedDict
from textwrap import dedent

from imdb import IMDb

from aslack import __author__, slack_bot, utils

INTERFACE = IMDb()


class Halliwell(slack_bot.SlackBot):
    """A bot to look up information on people in the movies."""

    INSTRUCTIONS = dedent("""
    Hello, I am an aSlack bot running on Cloud Foundry.

    For more information, see {aslack_url} or contact {author}.
    """.format(
        aslack_url='https://pythonhosted.org/aslack',
        author=__author__,
    ))

    def request_actor_information(self, data):
        """If you send me a message starting with the word 'person'"""
        return (self.message_is_to_me(data) and
                data['text'][len(self.address_as):].startswith('person'))

    def provide_actor_information(self, data):
        """I will tell you about the specified person."""
        name = data['text'].split(maxsplit=2)[-1]
        possible_people = INTERFACE.search_person(name, results=5)
        if not possible_people:
            text = 'Could not find {!r}'.format(name)
        else:
            person = possible_people[0]
            INTERFACE.update(person)
            bio = (person.get('bio') or ['&lt;no bio&gt;'])[0]
            text = dedent("""
            *{name}* (born {dob})

            {bio}

            See IMDb for more: {url}
            """.format(
                bio=utils.truncate(bio),
                dob=person.get('birth date', '&lt;unknown&gt;'),
                name=person.get('name', '&lt;unknown&gt;'),
                url='http://www.imdb.com/name/nm{}/'.format(person.personID),
            )).strip()
        return dict(
            channel=data['channel'],
            text=text,
        )

    MESSAGE_FILTERS = OrderedDict([
        (request_actor_information, provide_actor_information),
    ])
