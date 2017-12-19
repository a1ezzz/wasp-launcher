
import os
from setuptools import setup, find_packages

from wasp_launcher.version import __numeric_version__, __author__, __email__, __license__


class SetupPySpec:

	name = "wasp-launcher"
	version = __numeric_version__
	description = "Python applications launcher"
	keywords = ["wasp", "launcher", "web", "scheduler"]
	url = "https://github.com/a1ezzz/wasp-launcher"
	classifiers = [
		"Development Status :: 2 - Pre-Alpha",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 3.4",
		"Programming Language :: Python :: 3.5",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3 :: Only",
		"Topic :: Internet",
		"Topic :: Internet :: WWW/HTTP",
		"Topic :: Internet :: WWW/HTTP :: Dynamic Content",
		"Topic :: Internet :: WWW/HTTP :: HTTP Servers",
		"Topic :: Internet :: WWW/HTTP :: Session",
		"Topic :: Internet :: WWW/HTTP :: Site Management",
		"Topic :: Software Development"
	]
	# source - http://pypi.python.org/pypi?%3Aaction=list_classifiers
	zip_safe = False
	scripts = [
		'wasp-launcher.py',
		'wasp-launcher-cli.py'
	]
	extra_require = {}

	@staticmethod
	def require(fname):
		return open(fname).read().splitlines()

	@staticmethod
	def read(fname):
		return open(os.path.join(os.path.dirname(__file__), fname)).read()


if __name__ == "__main__":
	setup(
		name=SetupPySpec.name,
		version=SetupPySpec.version,
		author=__author__,
		author_email=__email__,
		maintainer=__author__,
		maintainer_email=__email__,
		description=SetupPySpec.description,
		license=__license__,
		keywords=SetupPySpec.keywords,
		url=SetupPySpec.url,
		packages=find_packages(),
		include_package_data=True,
		long_description=SetupPySpec.read('README'),
		classifiers=SetupPySpec.classifiers,
		install_requires=SetupPySpec.require('requirements.txt'),
		zip_safe=SetupPySpec.zip_safe,
		scripts=SetupPySpec.scripts,
		extras_require=SetupPySpec.extra_require
	)
