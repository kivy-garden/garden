from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(
        name='Kivy Garden',
        version='0.1.5',
        license='MIT',
        packages=['garden'],
        scripts=['bin/garden', 'bin/garden.bat'],
        install_requires=['requests'],
        )
