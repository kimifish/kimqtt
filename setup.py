from setuptools import setup, find_packages

setup(
    name='kiMQTT',
    version='0.1.4',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'paho-mqtt',
        'kimiutils',
    ],
    extras_require={
        'dev': [
            'pytest',
        ],
    },
)
