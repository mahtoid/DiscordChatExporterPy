import html
from PIL import ImageColor


async def escape_html(content):
    return html.escape(content)


async def member_colour_translator(member):
    if member is not None:
        user_colour = member.colour
        if '#000000' in str(user_colour):
            user_colour = f"color: #%02x%02x%02x;" % (255, 255, 255)
        else:
            user_colour = ImageColor.getrgb(str(user_colour))
            colour_r, colour_g, colour_b = user_colour
            user_colour = f"color: #%02x%02x%02x;" % (colour_r, colour_g, colour_b)
        return user_colour
    else:
        user_colour = f"color: #%02x%02x%02x;" % (255, 255, 255)
    return user_colour
