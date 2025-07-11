import datetime
import io
import pathlib
from typing import Union
import urllib.parse

from discord import Webhook, Attachment, File
import asyncio
import os

import aiohttp
from chat_exporter.ext.discord_import import discord


class AttachmentHandler:
	"""Handle the saving of attachments (images, videos, audio, etc.)

	Subclass this to implement your own asset handler."""

	async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored attachment.
		:param attachment: discord.Attachment
		:return: str
		"""
		raise NotImplementedError

class AttachmentToLocalFileHostHandler(AttachmentHandler):
	"""Save the assets to a local file host and embed the assets in the transcript from there."""

	def __init__(self, base_path: Union[str, pathlib.Path], url_base: str):
		if isinstance(base_path, str):
			base_path = pathlib.Path(base_path)
		self.base_path = base_path
		self.url_base = url_base

	async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored attachment.
		:param attachment: discord.Attachment
		:return: str
		"""
		file_name = urllib.parse.quote_plus(f"{datetime.datetime.utcnow().timestamp()}_{attachment.filename}")
		asset_path = self.base_path / file_name
		await attachment.save(asset_path)
		file_url = f"{self.url_base}/{file_name}"
		attachment.url = file_url
		attachment.proxy_url = file_url
		return attachment


class AttachmentToDiscordChannelHandler(AttachmentHandler):
	"""Save the attachment to a discord channel and embed the assets in the transcript from there."""

	def __init__(self, channel: discord.TextChannel):
		self.channel = channel

	async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored attachment.
		:param attachment: discord.Attachment
		:return: str
		"""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(attachment.url) as res:
					if res.status != 200:
						res.raise_for_status()
					data = io.BytesIO(await res.read())
					data.seek(0)
					attach = discord.File(data, attachment.filename)
					msg: discord.Message = await self.channel.send(file=attach)
					return msg.attachments[0]
		except discord.errors.HTTPException as e:
			# discords http errors, including missing permissions
			raise e
		
class AttachmentToWebhookHandler(AttachmentHandler):
	"""Save the attachment to a discord channel using webhook and embed the assets in the transcript from there."""

	def __init__(self, webhook_link: str) -> None:
		self.webhook_link = webhook_link
		self.size_limit = 8 * 1024 * 1024 # 8 MB = 8 * 1024 KB * 1024 B
		self.placeholder_path = os.path.join(os.path.dirname(__file__), "too_large.png")

	async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored attachment.
		:param attachment: discord.Attachment
		:return: str"""
		try:  
			if attachment.size > self.size_limit:
				file = File(self.placeholder_path, filename="too_large.png")
			else:
				file = await attachment.to_file()
				
			async with aiohttp.ClientSession() as session:
				webhook = Webhook.from_url(self.webhook_link, session=session)
				for i in range(3):
					try:
						message = await webhook.send(file=file, wait=True)
						break
					except aiohttp.ClientConnectionError:
						print(f"Retry {i+1}/3 | Error - Webhook connection failed.")
						await asyncio.sleep(3) # to prevent frequent retries on connection error

		except discord.errors.HTTPException as e:
			# discords http errors, including missing permissions
			raise e
		else:
			return message.attachments[0]