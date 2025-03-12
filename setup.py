from setuptools import setup, find_packages

setup(
    name='kiMQTT',
    version='0.1.3',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'paho-mqtt',
    ],
    extras_require={
        'dev': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
