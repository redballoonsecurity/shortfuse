#!/usr/bin/env python

from setuptools import setup

requirements = [
    'fusepy==2.0.4',
]

test_requirements = [
    'pytest==3.8.0',
    'sphinx==1.7.7',
    'sphinx-autobuild==0.7.1',
    'sphinx-rtd-theme==0.4.1',
    'xattr==0.9.6',
]

if __name__ == "__main__":
    module_name = 'shortfuse'
    module_version = '0.0.30'
    setup(
        name=module_name,
        version=module_version,
        description="shortfuse is a lightweight wrapper around fusepy",
        long_description=open('README.rst', 'r').read(),
        author='Red Balloon Security',
        author_email='quack-tech@redballoonsecurity.com',
        packages=[
            'shortfuse',
            'shortfuse.extra',
            'shortfuse_test'
        ],
        include_package_data=True,
        install_requires=requirements,
        tests_require=test_requirements,
    )
