from setuptools import setup, find_packages

setup(
    name='dfpyre',
    version='0.3.2',
    description='A package for externally creating code templates for the DiamondFire Minecraft server.',
    author='Amp',
    url='https://github.com/Amp63/pyre',
    license='MIT',
    keywords=['diamondfire', 'minecraft'],
    packages=find_packages(),
    package_data={'dfpyre': ['data/data.json']}
)