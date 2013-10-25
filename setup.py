from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(
        name='Kivy Garden',
        version='0.1',
        license='MIT',
        scripts=['garden', 'garden.bat'],
        install_requires=['requests'],
        )
