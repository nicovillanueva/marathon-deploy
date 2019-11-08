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
        'console_scripts': ['marathon-deploy = marathon_deploy.deploy:cli',
                            'marathon-check = marathon_deploy.checkappdeploy:main'],
    },
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: User Interfaces',
        'Environment :: Console',
    ],
)
