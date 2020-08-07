from setuptools import setup, find_packages
import os

requirements = [
        'pygame>=1.9,<2',
    ]
if os.name == 'nt':
    requirements.append('pywin32')

setup(
    name='edcompanion',
    version='0.1.5',
    url='https://github.com/djaney/edcompanion',
    author='Djane Rey Mabelin',
    author_email='thedjaney@gmail.com',
    description='Creates a streaming overlay for Elite: Dangerous',
    python_requires=">=3.5",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'edcompanion=scripts.edcompanion:main',
        ]
    },
    package_data={
        "overlays": ["*.ttf"],
    }
)
