from setuptools import setup, find_packages, Extension

setup(
    name="whipper",
    use_scm_version=True,
    description="a secure cd ripper preferring accuracy over speed",
    author=['Thomas Vander Stichele', 'The Whipper Team'],
    maintainer=['The Whipper Team'],
    url='https://github.com/whipper-team/whipper',
    license='GPL3',
    python_requires='>=3.5',
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    ext_modules=[
        Extension('accuraterip',
                  libraries=['sndfile'],
                  sources=['src/accuraterip-checksum.c'])
    ],
    extras_require={
        'cover_art': ["pillow"]
    },
    entry_points={
        'console_scripts': [
            'whipper = whipper.command.main:main'
         ]
    },
    data_files=[
        ('share/metainfo', ['com.github.whipper_team.Whipper.metainfo.xml']),
    ],
    scripts=[
        'scripts/accuraterip-checksum',
    ],
)
