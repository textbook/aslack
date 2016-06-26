"""Generic message handling functionality."""
from textwrap import dedent


class MessageHandler:
    """Base class for message handlers.

    Arguments:
      *_ (:py:class:`tuple`): Arbitrary positional arguments.

    Attributes:
      steps (:py:class:`list`): The local copy of the steps.
      STEPS (:py:class:`list`): The steps to take for each message.

    """

    def __init__(self, *_):
        self.text = None

    async def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    def description(self):
        """A user-friendly description of the handler.

        Returns:
          :py:class:`str`: The handler's description.

        """
        return dedent('\n'.join(self.__doc__.splitlines()[1:])).strip()

    def matches(self, data):
        """Whether the handler should handle the current message.

        Args:
          data: The data representing the current message.

        Returns:
          :py:class:`bool`: Whether it should be handled.

        """
        self.text = data.get('text')
        return True


class BotMessageHandler(MessageHandler):
    """Base class for handlers of messages about the current bot.

    Arguments:
      bot (:py:class:`~.SlackBot`): The current bot.

    Attributes:
      PHRASE (:py:class:`str`): The phrase to match.

    """

    PHRASE = None

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def matches(self, data):
        if self.bot.message_is_to_me(data):
            message = data['text'][len(self.bot.address_as):].strip()
            if message.startswith(self.PHRASE):
                return super().matches(data)
        return False
