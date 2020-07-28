from setuptools import setup, find_packages

setup(
    name='EdOverlay',
    version='0.1.0',
    url='https://github.com/mypackage.git',
    author='Djane Rey Mabelin',
    author_email='thedjaney@gmail.com',
    description='Description of my package',
    packages=find_packages(),
    install_requires=[
        'pygame>=1.9,<2'
    ],
    entrypoints={
        'console_scripts': [
            'edoverlay = bin.edoverlay:main',
        ]
  },
    package_data={
        "overlays": ["*.ttf"],
    }
)
