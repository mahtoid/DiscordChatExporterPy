<div align="center">

[![Version][pypi-version]][pypi-url]
[![Language][language-dom]][github-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![GPL License][license-shield]][license-url]


  <h2>DiscordChatExporterPy</h2>

  <p>
    Export Discord chats with your discord.py (or fork) bots!
    <br />
    <a href="https://discord.mahto.id/">Join Discord</a>
    ·
    <a href="https://github.com/mahtoid/DiscordChatExporterPy/issues/new?assignees=&labels=bug&template=bug-report.yml">Report Bug</a>
    ·
    <a href="https://github.com/mahtoid/DiscordChatExporterPy/issues/new?assignees=&labels=enhancement&template=feature-request.yml">Request Feature</a>
  </p>
</div>

---
## Installation

To install the library to your virtual environment, for bot usage, run the command:
```sh 
pip install chat-exporter
```

To clone the repository locally, run the command:
```sh
git clone https://github.com/mahtoid/DiscordChatExporterPy
```

<p align="right">(<a href="#top">back to top</a>)</p>

---
## Usage

There are currently 3 methods (functions) to `chat-exporter` which you can use to export your chat.<br/>
_Expand the blocks below to learn the functions, arguments and usages._
<details><summary><b>Basic Usage</b></summary>

`.quick_export()` is the simplest way of using chat-exporter.

Using the _quick_export_ function will gather the history of the channel you give, build the transcript then post the file and embed directly to the channel - returning a message object gathered from the message it posted.

This is mostly seen as a demo function, as opposed to a command you should actually use. 

**Required Argument(s):**<br/>
`channel`: `discord.TextChannel` object, whether `ctx.channel` or any channel you gather.

**Optional Argument(s):**<br/>
`bot`: `commands.Bot` object to gather members who are no longer in your guild.

**Return Argument:**<br/>
`discord.Message`: The message _quick_export_ will send, containing the embed and exported chat file.

**Example:**
```python
import discord
import chat_exporter
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

...

@bot.command()
async def save(ctx: commands.Context):
    await chat_exporter.quick_export(ctx.channel)

...
```

</details>

<details><summary><b>Customisable Usage</b></summary>

`.export()` is the most efficient and flexible method to export a chat using chat-exporter.

Using the _export_ function will generate a transcript using the channel you pass in, along with using any of the custom kwargs passed in to set limits, timezone, 24h formats and more (listed below).

This would be the main function to use within chat-exporter.

**Required Argument(s):**<br/>
`channel`: `discord.TextChannel` object, whether `ctx.channel` or any channel you gather.

**Optional Argument(s):**<br/>
`limit`: Integer value to set the limit (amount of messages) the chat exporter gathers when grabbing the history (default=unlimited).<br/>
`tz_info`: String value of a [TZ Database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) to set a custom timezone for the exported messages (default=UTC).<br/>
`guild`: `discord.Guild` object which can be passed in to solve bugs for certain forks.<br/>
`military_time`: Boolean value to set a 24h format for times within your exported chat (default=False | 12h format).<br/>
`fancy_times`: Boolean value which toggles the 'fancy times' (Today|Yesterday|Day).<br/>
`before`: `datetime.datetime` object which allows to gather messages from before a certain date.<br/>
`after`: `datetime.datetime` object which allows to gather messages from after a certain date.<br/>
`bot`: `commands.Bot` object to gather members who are no longer in your guild.<br/>
`attachment_handler`: `chat_exporter.AttachmentHandler` object to export assets to in order to make them available after the `channel` got deleted.<br/>

**Return Argument:**<br/>
`transcript`: The HTML build-up for you to construct the HTML File with Discord.

**Example:**
```python
import io

...

@bot.command()
async def save(ctx: commands.Context, limit: int = 100, tz_info: str = "UTC", military_time: bool = True):
    transcript = await chat_exporter.export(
        ctx.channel,
        limit=limit,
        tz_info=tz_info,
        military_time=military_time,
        bot=bot,
    )

    if transcript is None:
        return

    transcript_file = discord.File(
        io.BytesIO(transcript.encode()),
        filename=f"transcript-{ctx.channel.name}.html",
    )

    await ctx.send(file=transcript_file)
```
</details>
<details><summary><b>Raw Usage</b></summary>

`.raw_export()` is for the crazy people who like to do their own thing when using chat-exporter.

Using the _raw_export_ function will generate a transcript using the list of messages you pass in, along with using any of the custom kwargs passed in to set limits, timezone, 24h formats and more (listed below).

This would be for people who want to filter what content to export.

**Required Argument(s):**<br/>
`channel`: `discord.TextChannel` object, whether `ctx.channel` or any channel you gather (this is just for padding the header).<br/>
`messages`: A list of Message objects which you wish to export to an HTML file.

**Optional Argument(s):**<br/>
`tz_info`: String value of a [TZ Database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) to set a custom timezone for the exported messages (default=UTC)<br/>
`military_time`: Boolean value to set a 24h format for times within your exported chat (default=False | 12h format)<br/>
`fancy_times`: Boolean value which toggles the 'fancy times' (Today|Yesterday|Day)<br/>
`bot`: `commands.Bot` object to gather members who are no longer in your guild.
`attachment_handler`: `chat_exporter.AttachmentHandler` object to export assets to in order to make them available after the `channel` got deleted.<br/>

**Return Argument:**<br/>
`transcript`: The HTML build-up for you to construct the HTML File with Discord.

**Example:**
```python
import io

...

@bot.command()
async def purge(ctx: commands.Context, tz_info: str, military_time: bool):
    deleted_messages = await ctx.channel.purge()

    transcript = await chat_exporter.raw_export(
        ctx.channel,
        messages=deleted_messages,
        tz_info=tz_info,
        military_time=military_time,
        bot=bot,
    )

    if transcript is None:
        return

    transcript_file = discord.File(
        io.BytesIO(transcript.encode()),
        filename=f"transcript-{ctx.channel.name}.html",
    )

    await ctx.send(file=transcript_file)
```
</details>


<p align="right">(<a href="#top">back to top</a>)</p>

---
## Attachment Handler

Due to Discords newly introduced restrictions on to their CDN, we have introduced an Attachment Handler. This handler
will assist you with circumventing the 'broken' and 'dead-assets' which arise when former attachments hosted by Discord
reach their expiration date.

The `AttachmentHandler` serves as a template for you to implement your own asset handler. Below are two basic examples on
how to use the `AttachmentHandler`. One using the example of storing files on a local webserver, with the other being
an example of storing them on Discord *(the latter merely just being an example, this will still obviously run in to
the expiration issue)*.

If you do not specify an attachment handler, chat-exporter will continue to use the (proxy) URLs for the assets.

<details><summary><b>Concept</b></summary>

The concept of implementing such an AttachmentHandler is very easy. In the following a short general procedure is 
described to write your own AttachmentHandler fitting your storage solution. Here we will assume, that we store the 
attachments in a cloud storage.

1. Subclassing
Start by subclassing `chat_exporter.AttachmentHandler` and implement the `__init__` method if needed. This should look 
something like this:

```python
from chat_exporter import AttachmentHandler
from cloud_wrapper import CloudClient


class MyAttachmentHandler(AttachmentHandler):
    def __init__(self, *args, **kwargs):
        # Your initialization code here
        # in your case we just create the cloud client
        self.cloud_client = CloudClient()

```

2. Overwrite process_asset
The `process_asset` method is the method that is called for each asset in the chat. Here we have to implement the 
upload logic and the generation of the asset url from the uploaded asset.
    
```python
import io
import aiohttp
from chat_exporter import AttachmentHandler
from cloud_wrapper import CloudClient
from discord import Attachment


class MyAttachmentHandler(AttachmentHandler):
    def __init__(self, *args, **kwargs):
        # Your initialization code here
        # in your case we just create the cloud client
        self.cloud_client = CloudClient()

    async def process_asset(self, attachment: Attachment):
        # Your upload logic here, in our example we just upload the asset to the cloud
        
        # first we need to authorize the client
        await self.cloud_client.authorize()
        
        # then we fetch the content of the attachment
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as res:
                if res.status != 200:
                    res.raise_for_status()
                data = io.BytesIO(await res.read())
        data.seek(0)
        
        # and upload it to the cloud, back we get some sort of identifier for the uploaded file
        asset_id = await self.cloud_client.upload(data)
        
        # now we can generate the asset url from the identifier
        asset_url = await self.cloud_client.get_share_url(asset_id, shared_with="everyone")
        
        # and set the proxy url attribute of the attachment to the generated url
        attachment.proxy_url = asset_url
        return attachment

```

Note
1. The `process_asset` method should return the attachment object with the proxy_url attribute set to the generated url.
2. The `process_asset` method should be an async method, as it is likely that you have to do some async operations 
   like fetching the content of the attachment or uploading it to the cloud.
3. You are free to add other methods in your class, and call them from `process_asset` if you need to do some 
   operations before or after the upload of the asset. But the `process_asset` method is the only method that is 
called from chat-exporter.

</details>

**Examples:**

<ol>
<details><summary>AttachmentToLocalFileHostHandler</summary>

Assuming you have a file server running, which serves the content of the folder `/usr/share/assets/` 
under `https://example.com/assets/`, you can easily use the `AttachmentToLocalFileHostHandler` like this:
```python
import io
import discord
from discord.ext import commands
import chat_exporter
from chat_exporter import AttachmentToLocalFileHostHandler

...

# Establish the file handler
file_handler = AttachmentToLocalFileHostHandler(
    base_path="/usr/share/assets",
    url_base="https://example.com/assets/",
)

@bot.command()
async def save(ctx: commands.Context):
    transcript = await chat_exporter.export(
        ctx.channel,
        attachment_handler=file_handler,
    )

    if transcript is None:
        return

    transcript_file = discord.File(
        io.BytesIO(transcript.encode()),
        filename=f"transcript-{ctx.channel.name}.html",
    )

    await ctx.send(file=transcript_file)

```
</details>

<details><summary>AttachmentToDiscordChannel</summary>

Assuming you want to store your attachments in a discord channel, you can use the `AttachmentToDiscordChannel`. 
Please note that discord recent changes regarding content links will result in the attachments links being broken 
after 24 hours. While this is therefor not a recommended way to store your attachments, it should give you a good 
idea how to perform asynchronous storing of the attachments.

```python
import io
import discord
from discord.ext import commands
import chat_exporter
from chat_exporter import AttachmentToDiscordChannel

...

# Establish the file handler
channel_handler = AttachmentToDiscordChannel(
    channel=bot.get_channel(CHANNEL_ID),
)

@bot.command()
async def save(ctx: commands.Context):
    transcript = await chat_exporter.export(
        ctx.channel,
        attachment_handler=channel_handler,
    )

    if transcript is None:
        return

    transcript_file = discord.File(
        io.BytesIO(transcript.encode()),
        filename=f"transcript-{ctx.channel.name}.html",
    )

    await ctx.send(file=transcript_file)

```
</details>
</ol>
<p align="right">(<a href="#top">back to top</a>)</p>

---
## Screenshots

<details><summary><b>General</b></summary>
<ol>
    <details><summary>Discord</summary>
    <img src="https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/channel_output.png">
    </details>
    <details><summary>Chat-Exporter</summary>
    <img src="https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/html_output.png">
    </details>
</ol>
</details>
<p align="right">(<a href="#top">back to top</a>)</p>

---
## Attributions

*This project borrows CSS and HTML code from [Tyrrrz's C# DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter/) repository.*

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- LINK DUMP -->
[pypi-version]: https://img.shields.io/pypi/v/chat-exporter?style=for-the-badge
[pypi-url]: https://pypi.org/project/chat-exporter/
[language-dom]: https://img.shields.io/github/languages/top/mahtoid/discordchatexporterpy?style=for-the-badge
[forks-shield]: https://img.shields.io/github/forks/mahtoid/DiscordChatExporterPy?style=for-the-badge
[forks-url]: https://github.com/mahtoid/DiscordChatExporterPy/
[stars-shield]: https://img.shields.io/github/stars/mahtoid/DiscordChatExporterPy?style=for-the-badge
[stars-url]: https://github.com/mahtoid/DiscordChatExporterPy/stargazers
[issues-shield]: https://img.shields.io/github/issues/mahtoid/DiscordChatExporterPy?style=for-the-badge
[issues-url]: https://github.com/mahtoid/DiscordChatExporterPy/issues
[license-shield]: https://img.shields.io/github/license/mahtoid/DiscordChatExporterPy?style=for-the-badge
[license-url]: https://github.com/mahtoid/DiscordChatExporterPy/blob/master/LICENSE
[github-url]: https://github.com/mahtoid/DiscordChatExporterPy/
