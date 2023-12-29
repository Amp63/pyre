from setuptools import setup, find_packages

VERSION = '0.4.1'

setup(
    name='dfpyre',
    version=VERSION,
    description='A package for externally creating code templates for the DiamondFire Minecraft server.',
    author='Amp',
    url='https://github.com/Amp63/pyre',
    license='MIT',
    keywords=['diamondfire', 'minecraft'],
    packages=find_packages(),
    package_data={'dfpyre': ['data/data.json']},
    install_requires=[
        'mcitemlib'
    ]
)