# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

%global pkg_name %{name}

%define with()          %{expand:%%{?with_%{1}:1}%%{!?with_%{1}:0}}
%define without()       %{expand:%%{?with_%{1}:0}%%{!?with_%{1}:1}}
%define bcond_with()    %{expand:%%{?_with_%{1}:%%global with_%{1} 1}}
%define bcond_without() %{expand:%%{!?_without_%{1}:%%global with_%{1} 1}}

%bcond_with tools

%{!?aprconf: %{expand: %%define aprconf %{_bindir}/apr-config}}
%{!?apxs: %{expand: %%define apxs %{_bindir}/apxs}}
%{!?libtool: %{expand: %%define libtool %{_libdir}/apr-1/build/libtool}}

%define aprincludes %(%{aprconf} --includes 2>/dev/null)

# Update commitid and serial when new sources and release version are available
%global commitid 1c14fc065bc133887fdde55cab954691b3dc3aac
%global serial 23

Name:      mod_jk
Epoch:     0
Version:   1.2.48
Release:   %{serial}%{?dist}
Summary:   Tomcat mod_jk connector for Apache

Group:     Internet/WWW/Servers
License:   ASL 2.0
URL:       http://tomcat.apache.org
Source0:   tomcat-connectors-%{commitid}.tar.gz
Source1:   %{pkg_name}.conf.sample
Source2:   uriworkermap.properties.sample
Source3:   workers.properties.sample
Source4:   %{pkg_name}-part.conf

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires: httpd

BuildRequires: httpd-devel
BuildRequires: apr-devel
BuildRequires: apr-util-devel
# 64 bit only natives on RHEL 9
ExcludeArch:   i386 i686
BuildRequires: perl
BuildRequires: java-devel >= 1.6.0
BuildRequires: jpackage-utils >= 0:1.5.38
BuildRequires: libtool
BuildRequires: xalan-j2 >= 2.7.0
BuildRequires: systemd
Obsoletes: mod_jk-ap24 < 0:1.2.48-21

%description
Tomcat-connectors (mod_jk) is a project that provides web server
connectors for the Apache Tomcat servlet engine.

%package manual
Summary: Tomcat %{pkg_name} connector manual
Group: Internet/WWW/Servers

%description manual
Tomcat %{pkg_name} connector manual.

%if %with tools
%package tools
Group: Internet/Log Analysis
Summary: Analysis and report tools for %{pkg_name}

%description tools
Miscellaneous %{pkg_name} analysis and report tools.
%endif

%prep
%setup -q -n tomcat-connectors-%{commitid}

%{__sed} -i -e 's|^(APXSCPPFLAGS=.*)$|$1 %{aprincludes}|' \
    native/common/Makefile.in

%build
# Adding the "-z,now" option in LDFLAGS in order to gain
# full RELRO support
LDFLAGS="$LDFLAGS -Wl,-z,now"
export LDFLAGS

set -e
pushd native
    ./buildconf.sh
    %configure --with-apxs="%{_bindir}/apxs"
    export LIBTOOL="`%{_bindir}/apxs -q LIBTOOL 2>/dev/null`"
    # Handle old apxs (without -q LIBTOOL), eg Red Hat 8.0 and 9.
    if test -z "$LIBTOOL"; then
        LIBTOOL="%{libtool}"
    fi
    make %{?_smp_mflags} \
    LIBTOOL="$LIBTOOL" \
    EXTRA_CFLAGS="$RPM_OPT_FLAGS" \
    EXTRA_CPPFLAGS="%{aprincludes}" \
    RHBUILD_CFLAGS="-DJK_RH_BUILD=-%{serial}"
popd

%install
%{!?aprconf: %{expand: %%define aprconf %{_bindir}/apr-config}}
%{!?apxs: %{expand: %%define apxs %{_bindir}/apxs}}
%{!?libtool: %{expand: %%define libtool %{_libdir}/apr-1/build/libtool}}

%define aplibdir %(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define apconfdir %(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define aprincludes %(%{aprconf} --includes 2>/dev/null)

%{__rm} -rf $RPM_BUILD_ROOT
# bz#2047969 start
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 %{SOURCE4} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -d -m 0755 %{buildroot}%{_rundir}/%{name}/
touch %{buildroot}%{_rundir}/%{name}.pid
chmod 0755 %{buildroot}%{_rundir}/%{name}.pid
# bz#2047969 end
install -d -m 755 $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/
install -p -m 0644 %{SOURCE1} %{SOURCE2} %{SOURCE3} $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/
%{__sed} -i -e 's|/usr/local/bin\b|%{_bindir}|' tools/reports/*.pl
command="s|/usr/local/bin\b|%{_bindir}|"
%{__sed} -i -e $command tools/reports/*.pl
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}/%{aplibdir}
%{__install} -p -m 0755 native/apache-2.0/%{pkg_name}.so \
        ${RPM_BUILD_ROOT}/%{aplibdir}/%{pkg_name}.so
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}/%{_bindir}
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}%{_rundir}/%{name}
%{__install} -d -m 0700 ${RPM_BUILD_ROOT}/%{_var}/cache/httpd/%{name}

# for tools
%if %with tools
%{__install} -p -m 0755 tools/reports/*.pl ${RPM_BUILD_ROOT}/%{_bindir}
%endif

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%files
%{!?apxs: %{expand: %%define apxs %{_bindir}/apxs}}
%define aplibdir %(%{apxs} -q LIBEXECDIR 2>/dev/null)
%defattr(-,root,root,-)
%doc native/LICENSE native/NOTICE native/README.txt
%{aplibdir}/*
%config(noreplace) %{_sysconfdir}/httpd/conf.d/*
%attr(0700,apache,apache) %dir %{_var}/cache/httpd/%{name}
# bz#2047969 start
%dir %{_rundir}/%{name}/
%verify(not size mtime md5) %{_rundir}/%{name}.pid
%{_tmpfilesdir}/%{name}.conf
# bz#2047969 end

%if %with tools
%files tools
%defattr(-,root,root,-)
%doc tools/reports/README.txt
%{_bindir}/*
%endif

%changelog
* Thu Jan 12 2023 Sokratis Zappis <szappis@rehdat.com> - 1.2.48-23
- Add entries for tmpfiles.d mechanism
- Remove /var/run legacy location
- Resolves: rhbz#2047969

* Tue Aug 24 2021 George Zaronikas <gzaronik@redhat.com> - 1.2.48-22
- Specifying exact NVR in Obsoletes to avoid conflict with -ap24 subpackage
- Resolves: #1963135

* Wed Aug 18 2021 George Zaronikas <gzaronik@redhat.com> - 1.2.48-21
- Moving Obsoletes out of pkg description
- Resolves: #1963135

* Mon Aug 16 2021 Coty Sutherland <csutherl@redhat.com> - 1.2.48-20
- Cleanup spec file and remove .redhat-N suffix from release
- Remove ap24 subpackage since we only need to build for one version of httpd

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 0:1.2.48-19.redhat_1.1
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Wed Aug 04 2021 Coty Sutherland <csutherl@redhat.com> - 1.2.48-19
- Update shm file location in conf

* Mon Aug 02 2021 Coty Sutherland <csutherl@redhat.com> - 1.2.48-18
- Fix broken test

* Mon Aug 02 2021 Coty Sutherland <csutherl@redhat.com> - 1.2.48-17
- Fix typo in tests.yml filename

* Fri Jul 30 2021 George Zaronikas <gzaronik@redhat.com> - 1.2.48-16
- Resolves: #1963135
