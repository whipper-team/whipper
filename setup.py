from setuptools import setup, find_packages
from os import system, makedirs, environ

import morituri

setup(
    name="whipper",
    version=morituri.__version__,
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'Joe Lametta', 'Samantha Baldwin'],
    maintainer=['Joe Lametta', 'Samantha Baldwin'],
    url='https://github.com/JoeLametta/whipper',
    license='GPL3',
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'whipper = morituri.command.main:main'
         ]
    }
)
