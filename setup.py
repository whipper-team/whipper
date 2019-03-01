from setuptools import setup, find_packages

setup(
    name="whipper",
    use_scm_version=True,
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'The Whipper Team'],
    maintainer=['The Whipper Team'],
    url='https://github.com/whipper-team/whipper',
    license='GPL3',
    python_requires='>=2.7,<3',
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    entry_points={
        'console_scripts': [
            'whipper = whipper.command.main:main'
         ]
    },
    data_files=[
        ('share/metainfo', ['com.github.whipper_team.Whipper.metainfo.xml']),
    ],
)
