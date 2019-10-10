import os
from setuptools import setup

ROOT = os.path.dirname(__file__)

def get_version():
    version = open(os.path.join(ROOT, 'marathon_deploy', 'version.py')).read()
    return version

setup(
    name='marathon-deploy',
    version=get_version(),
    description='CLI tool to manage deployment of applications to Marathon from JSON files',
    author='Nicolas Villanueva',
    author_email='villanueva.arg@gmail.com',
    packages=['marathon_deploy', 'marathon_deploy.utils'],
    install_requires=['marathon>=0.9.3'],
    entry_points={
        'console_scripts': ['deploy-marathon = marathon_deploy.deploytool:main',
                            'check-marathon = marathon_deploy.checkappdeploy:main'],
    },
    include_package_data=True,
    zip_safe=False
)
