from setuptools import setup, find_packages

setup(
    name='Tea5767Raspberrypi',
    version='0.1.0',
    author='Juh Starret',
    author_email='starretjuh@example.com',
    description='A Raspberry Pi driver for the TEA5767 FM radio chip with Morse code transmitter.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/starretjuh/Tea5767Raspberrypi',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
    install_requires=[
        'RPi.GPIO',
        'smbus-cffi',
        'quick2wire-api',
        'websocket-client',
    ],
    python_requires='>=3.6',
)