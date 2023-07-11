##################################################################################
# Copyright (c) 2016, Katie McLaughlin                                           #
# All rights reserved.                                                           #
#                                                                                #
# Redistribution and use in source and binary forms, with or without             #
# modification, are permitted provided that the following conditions are met:    #
#                                                                                #
# * Redistributions of source code must retain the above copyright notice, this  #
#   list of conditions and the following disclaimer.                             #
#                                                                                #
# * Redistributions in binary form must reproduce the above copyright notice,    #
#   this list of conditions and the following disclaimer in the documentation    #
#   and/or other materials provided with the distribution.                       #
#                                                                                #
# * Neither the name of octohatrack nor the names of its                         #
#   contributors may be used to endorse or promote products derived from         #
#   this software without specific prior written permission.                     #
#                                                                                #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"    #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE      #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE #
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE   #
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL     #
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR     #
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER     #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,  #
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE  #
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.           #
#                                                                                #
# Github: https://github.com/glasnt/emojificate                                  #
##################################################################################
import unicodedata
from grapheme import graphemes
import emoji
import aiohttp

from chat_exporter.ext.cache import cache


cdn_fmt = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/{codepoint}.png"


@cache()
async def valid_src(src):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(src) as resp:
                return resp.status == 200
    except aiohttp.ClientConnectorError:
        return False


def valid_category(char):
    try:
        return unicodedata.category(char) == "So"
    except TypeError:
        return False


async def codepoint(codes):
    # See https://github.com/twitter/twemoji/issues/419#issuecomment-637360325
    if "200d" not in codes:
        return "-".join([c for c in codes if c != "fe0f"])
    return "-".join(codes)


async def convert(char):
    if valid_category(char):
        name = unicodedata.name(char).title()
    else:
        if len(char) == 1:
            return char
        else:
            shortcode = emoji.demojize(char)
            name = shortcode.replace(":", "").replace("_", " ").replace("selector", "").title()

    src = cdn_fmt.format(codepoint=await codepoint(["{cp:x}".format(cp=ord(c)) for c in char]))

    if await valid_src(src):
        return f'<img class="emoji emoji--small" src="{src}" alt="{char}" title="{name}" aria-label="Emoji: {name}">'
    else:
        return char


async def convert_emoji(string):
    x = []
    for ch in graphemes(string):
        x.append(await convert(ch))
    return "".join(x)
