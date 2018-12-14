from setuptools import setup, find_packages
from whipper import __version__ as whipper_version

setup(
    name="whipper",
    version=whipper_version,
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'The Whipper Team'],
    maintainer=['The Whipper Team'],
    url='https://github.com/whipper-team/whipper',
    license='GPL3',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'whipper = whipper.command.main:main'
         ]
    },
    data_files=[
        ('share/metainfo', ['com.github.whipper_team.Whipper.metainfo.xml']),
    ],
)
