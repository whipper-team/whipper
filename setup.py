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
    install_requires=[
        'musicbrainzngs',
        'mutagen',
        'pycdio>0.20',
        'PyGObject',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'whipper = whipper.command.main:main'
         ]
    },
    data_files=[
        ('share/metainfo', ['com.github.whipper_team.Whipper.metainfo.xml']),
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa: E501
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Ripping',
    ],
)
