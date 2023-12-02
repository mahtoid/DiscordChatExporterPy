import datetime
import io
import pathlib
from typing import Union

import aiohttp
import discord


class AssetHandler(object):
	"""Handle the saving of assets (images, videos, audio, etc.)

	Subclass this to implement your own asset handler."""

	async def process_asset(self, asset: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored asset.
		:param asset: discord.Attachment
		:return: str
		"""
		raise NotImplementedError

class LocalFileHostHandler(AssetHandler):
	"""Save the assets to a local file host and embed the assets in the transcript from there."""

	def __init__(self, base_path: Union[str, pathlib.Path], url_base: str):
		if isinstance(base_path, str):
			base_path = pathlib.Path(base_path)
		self.base_path = base_path
		self.url_base = url_base

	async def process_asset(self, asset: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored asset.
		:param asset: discord.Attachment
		:return: str
		"""
		file_name = f"{datetime.datetime.utcnow()}_{asset.filename}"
		asset_path = self.base_path / file_name
		await asset.save(asset_path)
		file_url = f"{self.url_base}/{file_name}"
		asset.url = file_url
		asset.proxy_url = file_url
		return asset


class DiscordChannelHandler(AssetHandler):
	"""Save the assets to a discord channel and embed the assets in the transcript from there."""

	def __init__(self, channel: discord.TextChannel):
		self.channel = channel

	async def process_asset(self, asset: discord.Attachment) -> discord.Attachment:
		"""Implement this to process the asset and return a url to the stored asset.
		:param asset: discord.Attachment
		:return: str
		"""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(asset.url) as res:
					if res.status != 200:
						res.raise_for_status()
					data = io.BytesIO(await res.read())
					data.seek(0)
					attach = discord.File(data, asset.filename)
					msg: discord.Message = await self.channel.send(file=attach)
					return msg.attachments[0]
		except discord.errors.HTTPException as e:
			# discords http errors, including missing permissions
			raise e