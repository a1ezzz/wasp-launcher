
%define _topdir %(echo $PWD)

Name:		wasp-launcher
Version:	0.0.2
Release:	0
License:	GPL
Source:		https://github.com/a1ezzz/wasp-launcher/archive/v0.0.2.tar.gz
URL:		https://github.com/a1ezzz/wasp-launcher
Summary:	python library
Packager:	Ildar Gafurov <dev@binblob.com>

BuildArch:	noarch
BuildRequires:	python34-devel
BuildRequires:	python34-setuptools
Requires:	python34-wasp-general
#Requires:	python34-mongo
Requires:	python34-tornado
Provides:	python34-wasp-launcher

%description
some python library

%prep
%autosetup

%build
%py3_build

%install
%py3_install
cp wasp-launcher.py %{buildroot}/usr/bin
cp wasp-launcher-cli.py %{buildroot}/usr/bin

%files
%{python3_sitelib}/*
/usr/bin/wasp-launcher.py
/usr/bin/wasp-launcher-cli.py
