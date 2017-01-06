from setuptools import setup, find_packages
from morituri import __version__ as morituri_version

setup(
    name="whipper",
    version=morituri_version,
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'Joe Lametta', 'Samantha Baldwin'],
    maintainer=['Joe Lametta', 'Samantha Baldwin'],
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'whipper = morituri.command.main:main'
         ]
    }
)
