from chat_exporter.ext.sanitize import escape


async def discriminator(user: str, discriminator: str):
    if discriminator != "0":
        return f"{escape(user)}#{escape(discriminator)}"
    return escape(user)
