from setuptools import setup, find_packages

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
    name='wqsat_get',
    packages=find_packages(),
    version='0.1.0',
    description='Python package for downloading satellite images for water quality monitoring.',
    author='CSIC',
    license='Apache License 2.0',
    install_requires=reqs)