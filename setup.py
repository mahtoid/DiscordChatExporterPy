from setuptools import setup, find_packages

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="chat_exporter",
    version="2.3",
    author="mahtoid",
    author_email="info@mahto.id",
    description="A simple Discord chat exporter for Python Discord bots.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mahtoid/DiscordChatExporterPy",
    packages=find_packages(),
    package_data={'': [r'chat_exporter/html/*.html']},
    include_package_data=True,
    license="GPL",
    install_requires=["aiohttp", "pytz", "grapheme", "emoji"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords="chat exporter",
)
