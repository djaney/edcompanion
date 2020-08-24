from setuptools import setup, find_packages
import os

requirements = [
        'pygame>=1.9,<2',
        'tk-tools==0.13.0',
        'requests==2.24.0'
    ]
if os.name == 'nt':
    requirements.append('pywin32')

VERSION = '0.2.2'

setup(
    name='edcompanion',
    version=VERSION,
    url='https://github.com/djaney/edcompanion',
    author='Djane Rey Mabelin',
    author_email='thedjaney@gmail.com',
    description='Creates a streaming overlay for Elite: Dangerous',
    python_requires=">=3.5",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'gui_scripts': [
            'edcompanion-launcher=scripts.launcher:main',
            'edcompanion=scripts.edcompanion:main',
        ]
    },
    package_data={
        "overlays": ["*.ttf"],
    }
)
