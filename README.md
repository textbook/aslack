# aSlack

/əˈslæk/

**Asynchronous Slack API integration.**

[![ISC License](https://img.shields.io/badge/license-ISC-blue.svg)][license]

aSlack is a lightweight, asynchronous wrapper for Slack's Web and real-time
messaging APIs, designed to allow the easy development of Slack tools and bots
in Python. It defines two principal components:

- `SlackApi` - a wrapper around the Web API; and
- `SlackBot` - a messaging bot built on top of the real-time messaging API.

## Compatibility

aSlack uses `asyncio` with the `async` and `await` syntax, so is only compatible
with Python versions 3.5 and above.

  [license]: LICENSE