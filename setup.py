from setuptools import setup, find_packages

setup(
    name='edoverlay',
    version='0.1.0',
    url='https://github.com/mypackage.git',
    author='Djane Rey Mabelin',
    author_email='thedjaney@gmail.com',
    description='Creates a streaming overlay for Elite: Dangerous',
    python_requires=">=3.5",
    packages=find_packages(),
    install_requires=[
        'pygame>=1.9,<2'
    ],
    entry_points={
        'console_scripts': [
            'edoverlay=scripts.edoverlay:main',
        ]
    },
    package_data={
        "overlays": ["*.ttf"],
    }
)
