%global cern_version CERN_VERSION_PLACEHOLDER
%global cern_release CERN_RELEASE_PLACEHOLDER

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global service aardvark
%global rhosp 0

%global with_doc 1

%global common_desc \
Aardvark is preemtible orchestrator service. \
It is responsible for orchestrating preemptible instances in OpenStack. \
In order to do that, it reacts as soon as a build request fails in Nova while \
scheduling due to the fact that not enough resources are available.

Name:       openstack-aardvark
Epoch:      1
Version:    %{cern_version}
Release:    %{cern_release}%{?dist}
Summary:    Orchestrator for Preemptible Instances

Group:      Development/Libraries
License:    ASL 2.0
Source0:    %{name}-%{version}.tar.gz


BuildArch:      noarch
BuildRequires:  openstack-macros
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-pbr >= 2.0.0
BuildRequires:  git
BuildRequires:  python-six >= 1.10.0
BuildRequires:  systemd

Requires:       python-aardvark = %{epoch}:%{version}-%{release}

%description
%{common_desc}


%package -n     python-%{service}
Summary:        Aardvark Python libraries
Provides:       python-%{name} = %{version}-%{release}
Requires:       python2-alembic >= 0.8.10
Requires:       python2-keystoneclient >= 3.15.0
Requires:       python2-keystoneauth1 >= 3.4.0
Requires:       python2-novaclient >= 1:9.1.0
Requires:       python2-oslo-concurrency >= 3.26.0
Requires:       python2-oslo-config >= 2:5.2.0
Requires:       python2-oslo-db >= 4.27.0
Requires:       python2-oslo-log >= 3.36.0
Requires:       python2-oslo-messaging >= 5.29.0
Requires:       python2-oslo-context >= 2.19.2
Requires:       python2-taskflow >= 2.16.0
Requires:       python2-stevedore >= 1.20.0
Requires:       python2-sqlalchemy >= 1.0.10

%description -n python-%{service}
%{common_desc}

This package contains the Python libraries.

%prep
%autosetup -n %{name}-%{upstream_version} -S git
%py_req_cleanup

%build
#PYTHONPATH=. oslo-config-generator --config-file=config-generator/aardvark.conf
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}

mkdir -p %{buildroot}/etc/aardvark/
mkdir -p %{buildroot}/var/log/aardvark

install -p -D -m 644 configfiles/aardvark-reaper.service %{buildroot}%{_unitdir}/aardvark-reaper.service
install -p -D -m 640 etc/aardvark.conf.sample %{buildroot}%{_sysconfdir}/aardvark/aardvark.conf
install -p -D -m 644 configfiles/openstack-aardvark.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/openstack-aardvark
chmod +x %{buildroot}/usr/bin/aardvark*

%pre
USERNAME=aardvark
GROUPNAME=$USERNAME
HOMEDIR=/home/$USERNAME
getent group $GROUPNAME >/dev/null || groupadd -r $GROUPNAME
getent passwd $USERNAME >/dev/null ||
    useradd -r -g $GROUPNAME -G $GROUPNAME -d $HOMEDIR -s /sbin/nologin \
            -c "Aardvark Daemons" $USERNAME
exit 0

%post
%systemd_post aardvark-reaper.service
%preun
%systemd_preun aardvark-reaper.service
%postun
%systemd_postun_with_restart aardvark-reaper.service

%files
%config(noreplace) %attr(-, root, root) %{_unitdir}/aardvark-reaper.service
%dir %{_sysconfdir}/aardvark
%config(noreplace) %attr(-, aardvark, aardvark) %{_sysconfdir}/aardvark/*
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-aardvark
%{_bindir}/aardvark*
%dir %attr(750, aardvark, aardvark) /var/log/aardvark

%files -n python-%{service}
%{python2_sitelib}/%{service}
%{python2_sitelib}/%{service}-*.egg-info


%changelog
* Thu Aug 2 2018 Theodoros Tsioutsias <theodoros.tsioutsias@cern.ch> 1:0.0.1
- Initial rpm attempt

