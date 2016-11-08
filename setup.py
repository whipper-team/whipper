from setuptools import setup, find_packages
from os import system, makedirs, environ

setup(
    name="whipper",
    version="0.4.0",
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'Joe Lametta', 'Samantha Baldwin'],
    maintainer=['Joe Lametta', 'Samantha Baldwin'],
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'whipper = morituri.rip.main:main'
         ]
    }
)
