from setuptools import setup, find_packages
from whipper import __version__ as whipper_version

setup(
    name="whipper",
    version=whipper_version,
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'Joe Lametta', 'Samantha Baldwin'],
    maintainer=['Joe Lametta', 'Samantha Baldwin'],
    url='https://github.com/JoeLametta/whipper',
    license='GPL3',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'whipper = whipper.command.main:main'
        ]
    }
)
