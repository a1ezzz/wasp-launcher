
# TODO: replace keywords with valid value
# TODO: replace url with valid value
# TODO: populate classifiers with values from http://pypi.python.org/pypi?%3Aaction=list_classifiers
# TODO Populate requirements.txt (details: https://pip.pypa.io/en/stable/user_guide/#requirements-files)

import os
from setuptools import setup

from wasp_launcher.version import __version__, __author__, __email__, __license__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def require(fname):
	return open(fname).read().splitlines()


setup(
	name = "wasp-launcher",
	version = __version__,
	author = __author__,
	author_email = __email__,
	description = ("Intelectual network launcher"),
	license = __license__,
	keywords = "",
	url = "",
	packages=['wasp_launcher'],
	long_description=read('README'),
	classifiers=[],
	install_requires=require('requirements.txt')
)
