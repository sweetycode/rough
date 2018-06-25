import re
import ast
import os
from setuptools import setup


pkg_name = 'rough'

with open('{}/__init__.py'.format(pkg_name)) as f:
    ver = re.search('__version__\s*=\s*(.*)', f.read().decode('utf8')).group(1)
    version = str(ast.literal_eval(ver))


setup(
    name=pkg_name,
    version=version,
    packages=[pkg_name,],
    entry_points={
        'console_scripts': [
            '{pkg} = {pkg}.{pkg}:run'.format(pkg=pkg_name),
        ],
    },
    install_requires=['requests', 'click', 'lxml'],
)
