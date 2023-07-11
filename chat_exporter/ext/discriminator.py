async def discriminator(user: str, discriminator: str):
    if discriminator != "0":
        return f"{user}#{discriminator}"
    return user
