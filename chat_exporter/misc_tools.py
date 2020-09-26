import html


async def escape_html(content):
    return html.escape(content)


async def member_colour_translator(member):
    r_colour = 0
    g_colour = 0
    b_colour = 0
    try:
        for roles in member.roles:
            if roles.colour.r != 0:
                r_colour = roles.colour.r
                g_colour = roles.colour.g
                b_colour = roles.colour.b
            if roles.colour.g != 0:
                r_colour = roles.colour.r
                g_colour = roles.colour.g
                b_colour = roles.colour.b
            if roles.colour.b != 0:
                r_colour = roles.colour.r
                g_colour = roles.colour.g
                b_colour = roles.colour.b
    except AttributeError:
        pass
    if r_colour == 0 and g_colour == 0 and b_colour == 0:
        r_colour = 255
        g_colour = 255
        b_colour = 255
    user_colour = f"color: #%02x%02x%02x;" % (r_colour, g_colour, b_colour)
    return user_colour
