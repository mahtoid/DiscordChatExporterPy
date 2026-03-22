import unittest

from chat_exporter.parse.ast import AstParser


class TestAST(unittest.TestCase):
    def setUp(self):
        self.parser = AstParser()

    def test_basic_formatting(self):
        text = "**Bold** and *Italic* and __Underline__ and ~~Strikethrough~~"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(
            out,
            (
                '<strong>Bold</strong> and <em>Italic</em> and '
                '<span style="text-decoration: underline">Underline</span> and '
                '<span style="text-decoration: line-through">Strikethrough</span>'
            ),
        )



    def test_inline_code(self):
        text = "This is `inline code`"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(out, 'This is <span class="pre pre-inline">inline code</span>')

    def test_code_block(self):
        text = "```python\nprint('hello')\n```"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(out, "<div class=\"pre pre--multiline language-python\">print('hello')</div>")

    def test_single_line_quote(self):
        # Using html escaped &gt; for Discord's quote logic
        text = "&gt; Quote 1\n&gt; Quote 2"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(
            out,
            '<div class="quote"><div style="min-width: 0; flex: 1;">Quote 1<br>Quote 2</div></div>',
        )

    def test_multiline_blockquote(self):
        text = "&gt;&gt;&gt; Multiline\nQuote\nBlock"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(
            out,
            '<div class="quote"><div style="min-width: 0; flex: 1;">Multiline<br>Quote<br>Block</div></div>',
        )

    def test_heading_newline_stripping(self):
        text = "# Heading\n\n\n\nTest"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(out, "<h1>Heading</h1>Test")

    def test_subtext_newline_preservation(self):
        text = "-# And some subtext!\nTest"
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)
        self.assertEqual(out, "<small>And some subtext!</small><br>Test")

    def test_combined_edge_cases(self):
        # Simulate the full test message as Discord would escape it
        text = (
            "&gt; Blockquote line 1\n&gt; Blockquote line 2\n&gt;&gt;&gt; Multiline\nQuote\nBlock\n-# And some subtext!"
        )
        nodes = self.parser.parse(text)
        out = "".join(n.render() for n in nodes)

        # The two single-line quotes should be merged into one quote block
        self.assertIn("Blockquote line 1<br>Blockquote line 2", out)
        # The >>> multiline quote should consume the rest (including subtext)
        self.assertIn("Multiline<br>Quote<br>Block", out)
        # Subtext should be rendered in the multiline quote
        self.assertIn("<small>And some subtext!</small>", out)
        # All content should be inside quote wrappers
        self.assertIn('<div class="quote">', out)
        self.assertIn('<div style="min-width: 0; flex: 1;">', out)

    def test_mentions(self):
        # Mock guild and roles/channels
        class MockRole:
            def __init__(self, id, name, r, g, b):
                self.id = id
                self.name = name
                self.color = type('obj', (object,), {'r': r, 'g': g, 'b': b})

        class MockChannel:
            def __init__(self, id, name):
                self.id = id
                self.name = name

        class MockMember:
            def __init__(self, id, display_name):
                self.id = id
                self.display_name = display_name

        class MockGuild:
            def get_role(self, id):
                if id == 123:
                    return MockRole(123, "TestRole", 255, 0, 0)
                return None
            def get_channel(self, id):
                if id == 456:
                    return MockChannel(456, "test-channel")
                return None
            def get_member(self, id):
                if id == 789:
                    return MockMember(789, "TestMember")
                return None

        guild = MockGuild()

        # Test Channel Mention
        text = "<#456> and &lt;#456&gt;"
        nodes = self.parser.parse(text)
        out = "".join(n.render(guild) for n in nodes)
        self.assertIn('#test-channel', out)
        self.assertEqual(out.count('#test-channel'), 2)

        # Test Role Mention
        text = "<@&123> and &lt;@&amp;123&gt;"
        nodes = self.parser.parse(text)
        out = "".join(n.render(guild) for n in nodes)
        self.assertIn('@TestRole', out)
        self.assertIn('color: #ff0000', out)

        # Test Member Mention
        text = "<@789> and &lt;@!789&gt;"
        nodes = self.parser.parse(text)
        out = "".join(n.render(guild) for n in nodes)
        self.assertIn('@TestMember', out)

        # Test Everyone/Here
        text = "@everyone and @here"
        nodes = self.parser.parse(text)
        out = "".join(n.render(guild) for n in nodes)
        self.assertIn('@everyone', out)
        self.assertIn('@here', out)

        # Test Time Mention
        text = "<t:1614556800:R>"
        nodes = self.parser.parse(text)
        out = "".join(n.render(guild) for n in nodes)
        self.assertIn('unix-timestamp', out)
        self.assertIn('raw-content="&lt;t:1614556800:R&gt;"', out)


if __name__ == "__main__":
    unittest.main()
