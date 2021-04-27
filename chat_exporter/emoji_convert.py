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
import requests


__all__ = ["convert_emoji"]

cdn_fmt = "https://twemoji.maxcdn.com/v/latest/72x72/{codepoint}.png"


def valid_src(src):
    try:
        req = requests.head(src)
    except requests.exceptions.ConnectionError:
        return False
    return req.status_code == 200


def valid_category(char):
    try:
        return unicodedata.category(char) == "So"
    except TypeError:
        return False


def get_best_name(char):
    """
    unicode data does not recognise the grapheme,
    so try and parse something from emoji instead.
    """
    shortcode = emoji.demojize(char, use_aliases=True)

    # Roughly convert shortcode to screenreader-friendly sentence.
    return shortcode.replace(":", "").replace("_", " ").replace("selector", "").title()


def convert(char):
    def tag(a, b):
        return '%s="%s"' % (a, b)

    def codepoint(codes):
        # See https://github.com/twitter/twemoji/issues/419#issuecomment-637360325
        if "200d" not in codes:
            return "-".join([c for c in codes if c != "fe0f"])
        return "-".join(codes)

    if valid_category(char):
        # Is a Char, and a Symbol
        name = unicodedata.name(char).title()
    else:
        if len(char) == 1:
            # Is a Char, not a Symbol, we don't care.
            return char
        else:
            # Is probably a grapheme
            name = get_best_name(char)

    src = cdn_fmt.format(codepoint=codepoint(["{cp:x}".format(cp=ord(c)) for c in char]))

    # If twitter doesn't have an image for it, pretend it's not an emoji.
    if valid_src(src):
        return "".join(
            [
                '<img class="emoji emoji--small" ',
                tag(" src", src),
                tag(" alt", char),
                tag(" title", name),
                tag(" aria-label", "Emoji: %s" % name),
                ">",
            ]
        )
    else:
        return char


def convert_emoji(string):
    return "".join(convert(ch) for ch in graphemes(string))
