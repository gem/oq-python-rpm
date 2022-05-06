# Override default installation
%define _prefix /opt/openquake
# docdir must be outside our prefix
%define _docdir /usr/share/doc

# ==================
# Top-level metadata
# ==================

%global pybasever 3.9

# pybasever without the dot:
%global pyshortver 39

Name: oq-python%{pyshortver}
Summary: Version %{pybasever} of the Python interpreter for OpenQuake
URL: https://www.python.org/

#  WARNING  When rebasing to a new Python version,
#           remember to update the python3-docs package as well
%global general_version %{pybasever}.12
#global prerel ...
%global upstream_version %{general_version}%{?prerel}
Version: %{general_version}%{?prerel:~%{prerel}}
Release: 1%{?dist}
License: Python


# ==================================
# Conditionals controlling the build
# ==================================

# Note that the bcond macros are named for the CLI option they create.
# "%%bcond_without" means "ENABLE by default and create a --without option"

# When bootstrapping python3, we need to build setuptools.
# but setuptools BR python3-devel and that brings in python3-rpm-generators;
# python3-rpm-generators needs python3-setuptools, so we cannot have it yet.
#
# We also use the previous build of Python in "make regen-all"
# and in "distutils.tests.test_bdist_rpm".
#
# Procedure: https://fedoraproject.org/wiki/SIGs/Python/UpgradingPython
#
#   IMPORTANT: When bootstrapping, it's very likely the wheels for pip and
#   setuptools are not available. Turn off the rpmwheels bcond until
#   the two packages are built with wheels to get around the issue.
%bcond_with bootstrap

# Expensive optimizations (mainly, profile-guided optimizations)
%bcond_without optimizations

# https://fedoraproject.org/wiki/Changes/PythonNoSemanticInterpositionSpeedup
%bcond_without no_semantic_interposition

# Run the test suite in %%check
%bcond_without tests

# Main interpreter loop optimization
%bcond_without computed_gotos

# https://fedoraproject.org/wiki/Changes/Python_Upstream_Architecture_Names
# For a very long time we have converted "upstream architecture names" to "Fedora names".
# This made sense at the time, see https://github.com/pypa/manylinux/issues/687#issuecomment-666362947
# However, with manylinux wheels popularity growth, this is now a problem.
# Wheels built on a Linux that doesn't do this were not compatible with ours and vice versa.
# We now have a compatibility layer to workaround a problem,
# but we also no longer use the legacy arch names in Fedora 34+.
# This bcond controls the behavior. The defaults should be good for anybody.
%if 0%{?fedora} >= 34 || 0%{?rhel} >= 9
%bcond_with legacy_archnames
%else
%bcond_without legacy_archnames
%endif

# In RHEL 9+, we obsolete/provide Platform Python from regular Python
# This is only appropriate for the main Python build
%if 0%{?rhel} >= 9 && %{with main_python}
%bcond_without rhel8_compat_shims
%else
%bcond_with rhel8_compat_shims
%endif


# =====================
# General global macros
# =====================

# Make sure that the proper installation of python is used by macros
%define __python3 %{_bindir}/python%{pybasever}
%define __python %{__python3}

%global pkgname python%{pybasever}
%global exename python%{pybasever}

%global pylibdir %{_libdir}/python%{pybasever}
%global dynload_dir %{pylibdir}/lib-dynload

# ABIFLAGS, LDVERSION and SOABI are in the upstream configure.ac
# See PEP 3149 for some background: http://www.python.org/dev/peps/pep-3149/
%global ABIFLAGS_optimized %{nil}

%global LDVERSION_optimized %{pybasever}%{ABIFLAGS_optimized}

# When we use the upstream arch triplets, we convert them from the legacy ones
# This is reversed in prep when %%with legacy_archnames, so we keep both macros
%global platform_triplet_legacy %{_arch}-linux%{_gnu}
%global platform_triplet_upstream %{expand:%(echo %{platform_triplet_legacy} | sed -E \\
    -e 's/^arm(eb)?-linux-gnueabi$/arm\\1-linux-gnueabihf/' \\
    -e 's/^mips64(el)?-linux-gnu$/mips64\\1-linux-gnuabi64/' \\
    -e 's/^ppc(64)?(le)?-linux-gnu$/powerpc\\1\\2-linux-gnu/')}
%if %{with legacy_archnames}
%global platform_triplet %{platform_triplet_legacy}
%else
%global platform_triplet %{platform_triplet_upstream}
%endif

%global SOABI_optimized cpython-%{pyshortver}%{ABIFLAGS_optimized}-%{platform_triplet}


# All bytecode files are in a __pycache__ subdirectory, with a name
# reflecting the version of the bytecode.
# See PEP 3147: http://www.python.org/dev/peps/pep-3147/
# For example,
#   foo/bar.py
# has bytecode at:
#   foo/__pycache__/bar.cpython-%%{pyshortver}.pyc
#   foo/__pycache__/bar.cpython-%%{pyshortver}.opt-1.pyc
#   foo/__pycache__/bar.cpython-%%{pyshortver}.opt-2.pyc
%global bytecode_suffixes .cpython-%{pyshortver}*.pyc

# libmpdec (mpdecimal package in Fedora) is tightly coupled with the
# decimal module. We keep it bundled as to avoid incompatibilities
# with the packaged version.
# The version information can be found at Modules/_decimal/libmpdec/mpdecimal.h
# defined as MPD_VERSION.
%global libmpdec_version 2.5.0

# Python's configure script defines SOVERSION, and this is used in the Makefile
# to determine INSTSONAME, the name of the libpython DSO:
#   LDLIBRARY='libpython$(VERSION).so'
#   INSTSONAME="$LDLIBRARY".$SOVERSION
# We mirror this here in order to make it easier to add the -gdb.py hooks.
# (if these get out of sync, the payload of the libs subpackage will fail
# and halt the build)
%global py_SOVERSION 1.0
%global py_INSTSONAME_optimized libpython%{LDVERSION_optimized}.so.%{py_SOVERSION}


# Disable automatic bytecompilation. The python3 binary is not yet be
# available in /usr/bin when Python is built. Also, the bytecompilation fails
# on files that test invalid syntax.
%undefine py_auto_byte_compile

# =======================
# Build-time requirements
# =======================

# (keep this list alphabetized)
BuildRequires: autoconf
BuildRequires: bluez-libs-devel
BuildRequires: bzip2
BuildRequires: bzip2-devel
BuildRequires: desktop-file-utils
BuildRequires: expat-devel

BuildRequires: findutils
BuildRequires: gcc-c++
BuildRequires: git-core
BuildRequires: glibc-all-langpacks
BuildRequires: glibc-devel
BuildRequires: gmp-devel
BuildRequires: gnupg2
BuildRequires: libappstream-glib
BuildRequires: libffi-devel
BuildRequires: libnsl2-devel
BuildRequires: libtirpc-devel
BuildRequires: libGL-devel
BuildRequires: libuuid-devel
BuildRequires: libX11-devel
BuildRequires: make
BuildRequires: ncurses-devel

BuildRequires: openssl-devel
BuildRequires: pkgconfig
BuildRequires: readline-devel
BuildRequires: redhat-rpm-config
BuildRequires: sqlite-devel
BuildRequires: gdb

BuildRequires: tar
BuildRequires: tcl-devel
BuildRequires: tix-devel
BuildRequires: tk-devel
BuildRequires: tzdata

BuildRequires: xz-devel
BuildRequires: zlib-devel

BuildRequires: /usr/bin/dtrace

# workaround http://bugs.python.org/issue19804 (test_uuid requires ifconfig)
BuildRequires: /usr/sbin/ifconfig

%if %{without bootstrap}
# for make regen-all and distutils.tests.test_bdist_rpm
BuildRequires: python%{pybasever}
# for proper automatic provides
BuildRequires: python3-rpm-generators
%endif

# =======================
# Source code and patches
# =======================
Source0: %{url}ftp/python/%{general_version}/Python-%{upstream_version}.tar.xz
Source1: %{url}ftp/python/%{general_version}/Python-%{upstream_version}.tar.xz.asc
Source2: %{url}static/files/pubkeys.txt

# A simple script to check timestamps of bytecode files
# Run in check section with Python that is currently being built
# Originally written by bkabrda
Source8: check-pyc-timestamps.py

# Desktop menu entry for idle3
Source10: idle3.desktop

# AppData file for idle3
Source11: idle3.appdata.xml

# (Patches taken from github.com/fedora-python/cpython)

# 00001 # d06a8853cf4bae9e115f45e1d531d2dc152c5cc8
# Fixup distutils/unixccompiler.py to remove standard library path from rpath
# Was Patch0 in ivazquez' python3000 specfile
Patch1: 00001-rpath.patch

# 00111 # 93b40d73360053ca68b0aeec33b6a8ca167e33e2
# Don't try to build a libpythonMAJOR.MINOR.a
#
# Downstream only: not appropriate for upstream.
#
# See https://bugzilla.redhat.com/show_bug.cgi?id=556092
Patch111: 00111-no-static-lib.patch

# 00189 # a79a85be3f0ad45792d998aed1104c2c2a0ef729
# Instead of bundled wheels, use our RPM packaged wheels
#
# We keep them in /usr/share/python-wheels
#
# Downstream only: upstream bundles
# We might eventually pursuit upstream support, but it's low prio
Patch189: 00189-use-rpm-wheels.patch
# The following versions of setuptools/pip are bundled when this patch is not applied.
# The versions are written in Lib/ensurepip/__init__.py, this patch removes them.
# When the bundled setuptools/pip wheel is updated, the patch no longer applies cleanly.
# In such cases, the patch needs to be amended and the versions updated here:
%global pip_version 22.0.4
%global setuptools_version 58.1.0

# 00251 # 1b1047c14ff98eae6d355b4aac4df3e388813f62
# Change user install location
#
# Set values of prefix and exec_prefix in distutils install command
# to /usr/local if executable is /usr/bin/python* and RPM build
# is not detected to make pip and distutils install into separate location.
#
# Fedora Change: https://fedoraproject.org/wiki/Changes/Making_sudo_pip_safe
# Downstream only: Reworked in Fedora 36+/Python 3.10+ to follow https://bugs.python.org/issue43976
#
# pypa/distutils integration: https://github.com/pypa/distutils/pull/70
#
# Also set sysconfig._PIP_USE_SYSCONFIG = False, to force pip-upgraded-pip
# to respect this patched distutils install command.
# See https://bugzilla.redhat.com/show_bug.cgi?id=2014513
Patch251: 00251-change-user-install-location.patch

# 00328 # 367fdcb5a075f083aea83ac174999272a8faf75c
# Restore pyc to TIMESTAMP invalidation mode as default in rpmbuild
#
# Since Fedora 31, the $SOURCE_DATE_EPOCH is set in rpmbuild to the latest
# %%changelog date. This makes Python default to the CHECKED_HASH pyc
# invalidation mode, bringing more reproducible builds traded for an import
# performance decrease. To avoid that, we don't default to CHECKED_HASH
# when $RPM_BUILD_ROOT is set (i.e. when we are building RPM packages).
#
# See https://src.fedoraproject.org/rpms/redhat-rpm-config/pull-request/57#comment-27426
# Downstream only: only used when building RPM packages
# Ideally, we should talk to upstream and explain why we don't want this
Patch328: 00328-pyc-timestamp-invalidation-mode.patch

# 00353 # ab4cc97b643cfe99f567e3a03e5617b507183771
# Original names for architectures with different names downstream
#
# https://fedoraproject.org/wiki/Changes/Python_Upstream_Architecture_Names
#
# Pythons in RHEL/Fedora used different names for some architectures
# than upstream and other distros (for example ppc64 vs. powerpc64).
# This was patched in patch 274, now it is sedded if %%with legacy_archnames.
#
# That meant that an extension built with the default upstream settings
# (on other distro or as an manylinux wheel) could not been found by Python
# on RHEL/Fedora because it had a different suffix.
# This patch adds the legacy names to importlib so Python is able
# to import extensions with a legacy architecture name in its
# file name.
# It work both ways, so it support both %%with and %%without legacy_archnames.
#
# WARNING: This patch has no effect on Python built with bootstrap
# enabled because Python/importlib_external.h is not regenerated
# and therefore Python during bootstrap contains importlib from
# upstream without this feature. It's possible to include
# Python/importlib_external.h to this patch but it'd make rebasing
# a nightmare because it's basically a binary file.
Patch353: 00353-architecture-names-upstream-downstream.patch

# 00371 # 1fc313929648e9b543542de09f59c55e175ac45a
# Revert "bpo-1596321: Fix threading._shutdown() for the main thread (GH-28549) (GH-28589)"
#
# This reverts commit 94d19f606fa18a1c4d2faca1caf2f470a8ce6d46. It
# introduced regression causing FreeIPA's tests to fail.
#
# For more info see:
# https://bodhi.fedoraproject.org/updates/FEDORA-2021-e152ce5f31
# https://github.com/GrahamDumpleton/mod_wsgi/issues/730
Patch371: 00371-revert-bpo-1596321-fix-threading-_shutdown-for-the-main-thread-gh-28549-gh-28589.patch

# (New patches go here ^^^)
#
# When adding new patches to "python" and "python3" in Fedora, EL, etc.,
# please try to keep the patch numbers in-sync between all specfiles.
#
# More information, and a patch number catalog, is at:
#
#     https://fedoraproject.org/wiki/SIGs/Python/PythonPatches
#
# The patches are stored and rebased at:
#
#     https://github.com/fedora-python/cpython

# ==========================================
# Descriptions, and metadata for subpackages
# ==========================================

Provides: oq-python3
Provides: oq-python%{pyshortver}
Provides: oq-python%{pybasever} = %{version}-%{release}
Obsoletes: oq-python35 oq-python36 oq-python37 oq-python38

%description
Python %{pybasever} package for OpenQuake

# ======================================================
# The prep phase of the build:
# ======================================================

%prep
%gpgverify -k2 -s1 -d0
%autosetup -S git_am -N -n Python-%{upstream_version}

# Apply patches up to 188
%autopatch -M 188

# Apply the remaining patches
%autopatch -m 190

# Remove all exe files to ensure we are not shipping prebuilt binaries
# note that those are only used to create Microsoft Windows installers
# and that functionality is broken on Linux anyway
find -name '*.exe' -print -delete

# Remove bundled libraries to ensure that we're using the system copy.
rm -r Modules/expat

# Remove files that should be generated by the build
# (This is after patching, so that we can use patches directly from upstream)
rm configure pyconfig.h.in


# ======================================================
# Configuring and building the code:
# ======================================================

%build

# The build process embeds version info extracted from the Git repository
# into the Py_GetBuildInfo and sys.version strings.
# Our Git repository is artificial, so we don't want that.
# Tell configure to not use git.
export HAS_GIT=not-found

# Regenerate the configure script and pyconfig.h.in
autoconf
autoheader

# Remember the current directory (which has sources and the configure script),
# so we can refer to it after we "cd" elsewhere.
topdir=$(pwd)

# Get proper option names from bconds
%if %{with computed_gotos}
%global computed_gotos_flag yes
%else
%global computed_gotos_flag no
%endif

%if %{with optimizations}
%global optimizations_flag "--enable-optimizations"
%else
%global optimizations_flag "--disable-optimizations"
%endif

# Set common compiler/linker flags
# We utilize the %%extension_...flags macros here so users building C/C++
# extensions with our python won't get all the compiler/linker flags used
# in Fedora RPMs.
# Standard library built here will still use the %%build_...flags,
# Fedora packages utilizing %%py3_build will use them as well
# https://fedoraproject.org/wiki/Changes/Python_Extension_Flags
export CFLAGS="%{extension_cflags} -D_GNU_SOURCE -fPIC -fwrapv"
export CFLAGS_NODIST="%{build_cflags} -D_GNU_SOURCE -fPIC -fwrapv%{?with_no_semantic_interposition: -fno-semantic-interposition}"
export CXXFLAGS="%{extension_cxxflags} -D_GNU_SOURCE -fPIC -fwrapv"
export CPPFLAGS="$(pkg-config --cflags-only-I libffi)"
export OPT="%{extension_cflags} -D_GNU_SOURCE -fPIC -fwrapv"
export LINKCC="gcc"
export CFLAGS="$CFLAGS $(pkg-config --cflags openssl)"
export LDFLAGS="%{extension_ldflags} -g $(pkg-config --libs-only-L openssl)"
export LDFLAGS_NODIST="%{build_ldflags}%{?with_no_semantic_interposition: -fno-semantic-interposition} -g $(pkg-config --libs-only-L openssl)"
# We can build several different configurations of Python: regular and debug.
# Define a common function that does one build:
BuildPython() {
  ConfName=$1
  ExtraConfigArgs=$2
  MoreCFlags=$3

  # Each build is done in its own directory
  ConfDir=build/$ConfName
  echo STARTING: BUILD OF PYTHON FOR CONFIGURATION: $ConfName
  mkdir -p $ConfDir
  pushd $ConfDir

  # Normally, %%configure looks for the "configure" script in the current
  # directory.
  # Since we changed directories, we need to tell %%configure where to look.
  %global _configure $topdir/configure

  # A workaround for https://bugs.python.org/issue39761
  export DFLAGS=" "

%configure \
  --with-platlibdir=%{_lib} \
  --enable-ipv6 \
  --enable-shared \
  --with-computed-gotos=%{computed_gotos_flag} \
  --with-system-expat \
  --with-system-ffi \
  --enable-loadable-sqlite-extensions \
  --with-dtrace \
  --with-lto \
  --with-ssl-default-suites=openssl \
  $ExtraConfigArgs \
  %{nil}

%global flags_override EXTRA_CFLAGS="$MoreCFlags" CFLAGS_NODIST="$CFLAGS_NODIST $MoreCFlags"

%if %{without bootstrap}
  # Regenerate generated files (needs python3)
  %make_build %{flags_override} regen-all PYTHON_FOR_REGEN="python%{pybasever}"
%endif

  # Invoke the build
  %make_build %{flags_override}

  popd
  echo FINISHED: BUILD OF PYTHON FOR CONFIGURATION: $ConfName

}

# Call the above to build each configuration.

BuildPython optimized \
  "--with-ensurepip %{optimizations_flag}" \
  ""

# ======================================================
# Installing the built code:
# ======================================================

%install

# As in %%build, remember the current directory
topdir=$(pwd)

# Multilib support for pyconfig.h
# 32- and 64-bit versions of pyconfig.h are different. For multilib support
# (making it possible to install 32- and 64-bit versions simultaneously),
# we need to install them under different filenames, and to make the common
# "pyconfig.h" include the right file based on architecture.
# See https://bugzilla.redhat.com/show_bug.cgi?id=192747
# Filanames are defined here:
%global _pyconfig32_h pyconfig-32.h
%global _pyconfig64_h pyconfig-64.h
%global _pyconfig_h pyconfig-%{__isa_bits}.h

# Use a common function to do an install for all our configurations:
InstallPython() {

  ConfName=$1
  PyInstSoName=$2
  MoreCFlags=$3
  LDVersion=$4

  # Switch to the directory with this configuration's built files
  ConfDir=build/$ConfName
  echo STARTING: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
  mkdir -p $ConfDir
  pushd $ConfDir

  %make_install EXTRA_CFLAGS="$MoreCFlags"

  popd

  # Rename the -devel script that differs on different arches to arch specific name
  mv %{buildroot}%{_bindir}/python${LDVersion}-{,`uname -m`-}config
  echo -e '#!/bin/sh\nexec `dirname $0`/python'${LDVersion}'-`uname -m`-config "$@"' > \
    %{buildroot}%{_bindir}/python${LDVersion}-config
  echo '[ $? -eq 127 ] && echo "Could not find python'${LDVersion}'-`uname -m`-config. Look around to see available arches." >&2' >> \
    %{buildroot}%{_bindir}/python${LDVersion}-config
    chmod +x %{buildroot}%{_bindir}/python${LDVersion}-config

  # Make python3-devel multilib-ready
  mv %{buildroot}%{_includedir}/python${LDVersion}/pyconfig.h \
     %{buildroot}%{_includedir}/python${LDVersion}/%{_pyconfig_h}
  cat > %{buildroot}%{_includedir}/python${LDVersion}/pyconfig.h << EOF
#include <bits/wordsize.h>

#if __WORDSIZE == 32
#include "%{_pyconfig32_h}"
#elif __WORDSIZE == 64
#include "%{_pyconfig64_h}"
#else
#error "Unknown word size"
#endif
EOF

  echo FINISHED: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
}

# Now the optimized build:
InstallPython optimized \
  %{py_INSTSONAME_optimized} \
  "" \
  %{LDVERSION_optimized}

# Install directories for additional packages
install -d -m 0755 %{buildroot}%{pylibdir}/site-packages/__pycache__
%if "%{_lib}" == "lib64"
# The 64-bit version needs to create "site-packages" in /usr/lib/ (for
# pure-Python modules) as well as in /usr/lib64/ (for packages with extension
# modules).
# Note that rpmlint will complain about hardcoded library path;
# this is intentional.
install -d -m 0755 %{buildroot}%{_prefix}/lib/python%{pybasever}/site-packages/__pycache__
%endif

# Make sure distutils looks at the right pyconfig.h file
# See https://bugzilla.redhat.com/show_bug.cgi?id=201434
# Similar for sysconfig: sysconfig.get_config_h_filename tries to locate
# pyconfig.h so it can be parsed, and needs to do this at runtime in site.py
# when python starts up (see https://bugzilla.redhat.com/show_bug.cgi?id=653058)
#
# Split this out so it goes directly to the pyconfig-32.h/pyconfig-64.h
# variants:
sed -i -e "s/'pyconfig.h'/'%{_pyconfig_h}'/" \
  %{buildroot}%{pylibdir}/distutils/sysconfig.py \
  %{buildroot}%{pylibdir}/sysconfig.py

# Install pathfix.py to bindir
# See https://github.com/fedora-python/python-rpm-porting/issues/24
cp -p Tools/scripts/pathfix.py %{buildroot}%{_bindir}/pathfix%{pybasever}.py

# Install i18n tools to bindir
# They are also in python2, so we version them
# https://bugzilla.redhat.com/show_bug.cgi?id=1571474
for tool in pygettext msgfmt; do
  cp -p Tools/i18n/${tool}.py %{buildroot}%{_bindir}/${tool}%{pybasever}.py
  ln -s ${tool}%{pybasever}.py %{buildroot}%{_bindir}/${tool}3.py
done

# Switch all shebangs to refer to the specific Python version.
# This currently only covers files matching ^[a-zA-Z0-9_]+\.py$,
# so handle files named using other naming scheme separately.
LD_LIBRARY_PATH=./build/optimized ./build/optimized/python \
  Tools/scripts/pathfix.py \
  -i "%{_bindir}/python%{pybasever}" -pn \
  %{buildroot} \
  %{buildroot}%{_bindir}/*%{pybasever}.py \
  %{?with_gdb_hooks:%{buildroot}$DirHoldingGdbPy/*.py}

# Remove shebang lines from .py files that aren't executable, and
# remove executability from .py files that don't have a shebang line:
find %{buildroot} -name \*.py \
  \( \( \! -perm /u+x,g+x,o+x -exec sed -e '/^#!/Q 0' -e 'Q 1' {} \; \
  -print -exec sed -i '1d' {} \; \) -o \( \
  -perm /u+x,g+x,o+x ! -exec grep -m 1 -q '^#!' {} \; \
  -exec chmod a-x {} \; \) \)

# Get rid of DOS batch files:
find %{buildroot} -name \*.bat -exec rm {} \;

# Get rid of backup files:
find %{buildroot}/ -name "*~" -exec rm -f {} \;
find . -name "*~" -exec rm -f {} \;

# Do bytecompilation with the newly installed interpreter.
# This is similar to the script in macros.pybytecompile
# compile *.pyc
# Python CMD line options:
# -s - don't add user site directory to sys.path
# -B - don't write .pyc files on import
# compileall CMD line options:
# -f - force rebuild even if timestamps are up to date
# -o - optimization levels to run compilation with
# -s - part of path to left-strip from path to source file (buildroot)
# -p - path to add as prefix to path to source file (/ to make it absolute)
# --hardlink-dupes - hardlink different optimization level pycs together if identical (saves space)
LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
%{buildroot}%{_bindir}/python%{pybasever} -s -B -m compileall \
-f %{_smp_mflags} -o 0 -o 1 -o 2 -s %{buildroot} -p / %{buildroot} --hardlink-dupes || :

# Turn this BRP off, it is done by compileall2 --hardlink-dupes above
%global __brp_python_hardlink %{nil}

# Since we have pathfix.py in bindir, this is created, but we don't want it
rm -rf %{buildroot}%{_bindir}/__pycache__

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find %{buildroot} -perm 555 -exec chmod 755 {} \;

# There's 2to3-X.X executable and 2to3 soft link to it.
# No reason to have both, so keep only 2to3 as an executable.
# See https://bugzilla.redhat.com/show_bug.cgi?id=1111275
mv %{buildroot}%{_bindir}/2to3-%{pybasever} %{buildroot}%{_bindir}/2to3

%if %{without main_python}
# Remove stuff that would conflict with python3 package
rm %{buildroot}%{_bindir}/python3
rm %{buildroot}%{_bindir}/pydoc3
rm %{buildroot}%{_bindir}/pygettext3.py
rm %{buildroot}%{_bindir}/msgfmt3.py
rm %{buildroot}%{_bindir}/idle3
rm %{buildroot}%{_bindir}/python3-*
rm %{buildroot}%{_bindir}/2to3
rm %{buildroot}%{_libdir}/libpython3.so
rm %{buildroot}%{_mandir}/man1/python3.1*
rm %{buildroot}%{_libdir}/pkgconfig/python3.pc
rm %{buildroot}%{_libdir}/pkgconfig/python3-embed.pc
%else
# Link the unversioned stuff
# https://fedoraproject.org/wiki/Changes/Python_means_Python3
ln -s ./python3 %{buildroot}%{_bindir}/python
ln -s ./pydoc3 %{buildroot}%{_bindir}/pydoc
ln -s ./pygettext3.py %{buildroot}%{_bindir}/pygettext.py
ln -s ./msgfmt3.py %{buildroot}%{_bindir}/msgfmt.py
ln -s ./idle3 %{buildroot}%{_bindir}/idle
ln -s ./python3-config %{buildroot}%{_bindir}/python-config
ln -s ./python3.1 %{buildroot}%{_mandir}/man1/python.1
ln -s ./python3.pc %{buildroot}%{_libdir}/pkgconfig/python.pc
ln -s ./pathfix%{pybasever}.py %{buildroot}%{_bindir}/pathfix.py
%if %{with debug_build}
ln -s ./python3-debug %{buildroot}%{_bindir}/python-debug
%endif
%endif

# Remove large, autogenerated sources and keep only the non-optimized pycache
for file in %{buildroot}%{pylibdir}/pydoc_data/topics.py $(grep --include='*.py' -lr %{buildroot}%{pylibdir}/encodings -e 'Python Character Mapping Codec .* from .* with gencodec.py'); do
    directory=$(dirname ${file})
    module=$(basename ${file%%.py})
    mv ${directory}/{__pycache__/${module}.cpython-%{pyshortver}.pyc,${module}.pyc}
    rm ${directory}/{__pycache__/${module}.cpython-%{pyshortver}.opt-?.pyc,${module}.py}
done
# ======================================================
# Checks for packaging issues
# ======================================================

%check

# setuptools 60+ uses its own copy of distutils by default
# this setting must be overriden with the environment variable for
# Python tests to use the standard library's distutils
export SETUPTOOLS_USE_DISTUTILS=stdlib

# first of all, check timestamps of bytecode files
find %{buildroot} -type f -a -name "*.py" -print0 | \
    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} %{SOURCE8}

# Ensure that the curses module was linked against libncursesw.so, rather than
# libncurses.so
# See https://bugzilla.redhat.com/show_bug.cgi?id=539917
ldd %{buildroot}/%{dynload_dir}/_curses*.so \
    | grep curses \
    | grep libncurses.so && (echo "_curses.so linked against libncurses.so" ; exit 1)

# Ensure that the debug modules are linked against the debug libpython, and
# likewise for the optimized modules and libpython:
for Module in %{buildroot}/%{dynload_dir}/*.so ; do
    case $Module in
    *.%{SOABI_debug})
        ldd $Module | grep %{py_INSTSONAME_optimized} &&
            (echo Debug module $Module linked against optimized %{py_INSTSONAME_optimized} ; exit 1)

        ;;
    *.%{SOABI_optimized})
        ldd $Module | grep %{py_INSTSONAME_debug} &&
            (echo Optimized module $Module linked against debug %{py_INSTSONAME_debug} ; exit 1)
        ;;
    esac
done

# Verify that the bundled libmpdec version python was compiled with, is the same version we have virtual
# provides for in the SPEC.
test "$(LD_LIBRARY_PATH=$(pwd)/build/optimized $(pwd)/build/optimized/python -c 'import decimal; print(decimal.__libmpdec_version__)')" = \
     "%{libmpdec_version}"

# ======================================================
# Running the upstream test suite
# ======================================================

topdir=$(pwd)
CheckPython() {
  ConfName=$1
  ConfDir=$(pwd)/build/$ConfName

  echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

  # Note that we're running the tests using the version of the code in the
  # builddir, not in the buildroot.

  # Show some info, helpful for debugging test failures
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.pythoninfo

  # Run the upstream test suite
  # --timeout=1800: kill test running for longer than 30 minutes
  # test_distutils
  #   distutils.tests.test_bdist_rpm tests fail when bootstraping the Python
  #   package: rpmbuild requires /usr/bin/pythonX.Y to be installed
  # test_gdb on arm on Fedora 33:
  #   https://bugzilla.redhat.com/show_bug.cgi?id=1846390
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.regrtest \
    -wW --slowest -j0 --timeout=1800 \
    %if %{with bootstrap}
    -x test_distutils \
    %endif
    %ifarch %{mips64}
    -x test_ctypes \
    %endif
    %ifarch %{arm}
    %if 0%{?fedora} < 34 && 0%{?rhel} < 9
    -x test_gdb \
    %endif
    %endif

  echo FINISHED: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

}

%if %{with tests}

# Check each of the configurations:
%if %{with debug_build}
CheckPython debug
%endif # with debug_build
CheckPython optimized

%endif # with tests
# ======================================================
# Scriptlets
# ======================================================

%files
%doc README.rst

# In /opt/openquake we are the owners of bin, usr and so on
%dir %{_prefix}
%dir %{_bindir}
%dir %{_libdir}
%if "%{_lib}" == "lib64"
%dir %{_prefix}/lib
%endif
%dir %{_includedir}
%dir %{_datadir}
%dir %{pylibdir}
%dir %{dynload_dir}

%{pylibdir}/lib2to3
%if %{without flatpackage}
%exclude %{pylibdir}/lib2to3/tests
%endif

%dir %{pylibdir}/unittest/
%dir %{pylibdir}/unittest/__pycache__/
%{pylibdir}/unittest/*.py
%{pylibdir}/unittest/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/asyncio/
%dir %{pylibdir}/asyncio/__pycache__/
%{pylibdir}/asyncio/*.py
%{pylibdir}/asyncio/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/venv/
%dir %{pylibdir}/venv/__pycache__/
%{pylibdir}/venv/*.py
%{pylibdir}/venv/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/venv/scripts

%{pylibdir}/wsgiref
%{pylibdir}/xmlrpc

%dir %{pylibdir}/ensurepip/
%dir %{pylibdir}/ensurepip/__pycache__/
%{pylibdir}/ensurepip/*.py
%{pylibdir}/ensurepip/__pycache__/*%{bytecode_suffixes}

%if %{with rpmwheels}
%exclude %{pylibdir}/ensurepip/_bundled
%else
%dir %{pylibdir}/ensurepip/_bundled
%{pylibdir}/ensurepip/_bundled/*.whl
%{pylibdir}/ensurepip/_bundled/__init__.py
%{pylibdir}/ensurepip/_bundled/__pycache__/*%{bytecode_suffixes}
%endif

%dir %{pylibdir}/concurrent/
%dir %{pylibdir}/concurrent/__pycache__/
%{pylibdir}/concurrent/*.py
%{pylibdir}/concurrent/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/concurrent/futures/
%dir %{pylibdir}/concurrent/futures/__pycache__/
%{pylibdir}/concurrent/futures/*.py
%{pylibdir}/concurrent/futures/__pycache__/*%{bytecode_suffixes}

%{pylibdir}/pydoc_data

%{dynload_dir}/_blake2.%{SOABI_optimized}.so
%{dynload_dir}/_md5.%{SOABI_optimized}.so
%{dynload_dir}/_sha1.%{SOABI_optimized}.so
%{dynload_dir}/_sha256.%{SOABI_optimized}.so
%{dynload_dir}/_sha3.%{SOABI_optimized}.so
%{dynload_dir}/_sha512.%{SOABI_optimized}.so

%{dynload_dir}/_asyncio.%{SOABI_optimized}.so
%{dynload_dir}/_bisect.%{SOABI_optimized}.so
%{dynload_dir}/_bz2.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_cn.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_hk.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_iso2022.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_jp.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_kr.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_tw.%{SOABI_optimized}.so
%{dynload_dir}/_contextvars.%{SOABI_optimized}.so
%{dynload_dir}/_crypt.%{SOABI_optimized}.so
%{dynload_dir}/_csv.%{SOABI_optimized}.so
%{dynload_dir}/_ctypes.%{SOABI_optimized}.so
%{dynload_dir}/_curses.%{SOABI_optimized}.so
%{dynload_dir}/_curses_panel.%{SOABI_optimized}.so
%{dynload_dir}/_dbm.%{SOABI_optimized}.so
%{dynload_dir}/_decimal.%{SOABI_optimized}.so
%{dynload_dir}/_elementtree.%{SOABI_optimized}.so
%if %{with gdbm}
%{dynload_dir}/_gdbm.%{SOABI_optimized}.so
%endif
%{dynload_dir}/_hashlib.%{SOABI_optimized}.so
%{dynload_dir}/_heapq.%{SOABI_optimized}.so
%{dynload_dir}/_json.%{SOABI_optimized}.so
%{dynload_dir}/_lsprof.%{SOABI_optimized}.so
%{dynload_dir}/_lzma.%{SOABI_optimized}.so
%{dynload_dir}/_multibytecodec.%{SOABI_optimized}.so
%{dynload_dir}/_multiprocessing.%{SOABI_optimized}.so
%{dynload_dir}/_opcode.%{SOABI_optimized}.so
%{dynload_dir}/_pickle.%{SOABI_optimized}.so
%{dynload_dir}/_posixsubprocess.%{SOABI_optimized}.so
%{dynload_dir}/_queue.%{SOABI_optimized}.so
%{dynload_dir}/_random.%{SOABI_optimized}.so
%{dynload_dir}/_socket.%{SOABI_optimized}.so
%{dynload_dir}/_sqlite3.%{SOABI_optimized}.so
%{dynload_dir}/_ssl.%{SOABI_optimized}.so
%{dynload_dir}/_statistics.%{SOABI_optimized}.so
%{dynload_dir}/_struct.%{SOABI_optimized}.so
%{dynload_dir}/array.%{SOABI_optimized}.so
%{dynload_dir}/audioop.%{SOABI_optimized}.so
%{dynload_dir}/binascii.%{SOABI_optimized}.so
%{dynload_dir}/cmath.%{SOABI_optimized}.so
%{dynload_dir}/_datetime.%{SOABI_optimized}.so
%{dynload_dir}/fcntl.%{SOABI_optimized}.so
%{dynload_dir}/grp.%{SOABI_optimized}.so
%{dynload_dir}/math.%{SOABI_optimized}.so
%{dynload_dir}/mmap.%{SOABI_optimized}.so
%{dynload_dir}/nis.%{SOABI_optimized}.so
%{dynload_dir}/ossaudiodev.%{SOABI_optimized}.so
%{dynload_dir}/parser.%{SOABI_optimized}.so
%{dynload_dir}/_posixshmem.%{SOABI_optimized}.so
%{dynload_dir}/pyexpat.%{SOABI_optimized}.so
%{dynload_dir}/readline.%{SOABI_optimized}.so
%{dynload_dir}/resource.%{SOABI_optimized}.so
%{dynload_dir}/select.%{SOABI_optimized}.so
%{dynload_dir}/spwd.%{SOABI_optimized}.so
%{dynload_dir}/syslog.%{SOABI_optimized}.so
%{dynload_dir}/termios.%{SOABI_optimized}.so
%{dynload_dir}/unicodedata.%{SOABI_optimized}.so
%{dynload_dir}/_uuid.%{SOABI_optimized}.so
%{dynload_dir}/xxlimited.%{SOABI_optimized}.so
%{dynload_dir}/_xxsubinterpreters.%{SOABI_optimized}.so
%{dynload_dir}/zlib.%{SOABI_optimized}.so
%{dynload_dir}/_zoneinfo.%{SOABI_optimized}.so

%dir %{pylibdir}/site-packages/
%dir %{pylibdir}/site-packages/__pycache__/
%{pylibdir}/site-packages/README.txt
%{pylibdir}/*.py
%dir %{pylibdir}/__pycache__/
%{pylibdir}/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/collections/
%dir %{pylibdir}/collections/__pycache__/
%{pylibdir}/collections/*.py
%{pylibdir}/collections/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/ctypes/
%dir %{pylibdir}/ctypes/__pycache__/
%{pylibdir}/ctypes/*.py
%{pylibdir}/ctypes/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/ctypes/macholib

%{pylibdir}/curses

%dir %{pylibdir}/dbm/
%dir %{pylibdir}/dbm/__pycache__/
%{pylibdir}/dbm/*.py
%{pylibdir}/dbm/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/distutils/
%dir %{pylibdir}/distutils/__pycache__/
%{pylibdir}/distutils/*.py
%{pylibdir}/distutils/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/distutils/README
%{pylibdir}/distutils/command

%dir %{pylibdir}/email/
%dir %{pylibdir}/email/__pycache__/
%{pylibdir}/email/*.py
%{pylibdir}/email/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/email/mime
%doc %{pylibdir}/email/architecture.rst

%{pylibdir}/encodings

%{pylibdir}/html
%{pylibdir}/http

%dir %{pylibdir}/importlib/
%dir %{pylibdir}/importlib/__pycache__/
%{pylibdir}/importlib/*.py
%{pylibdir}/importlib/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/json/
%dir %{pylibdir}/json/__pycache__/
%{pylibdir}/json/*.py
%{pylibdir}/json/__pycache__/*%{bytecode_suffixes}

%{pylibdir}/logging
%{pylibdir}/multiprocessing

%dir %{pylibdir}/sqlite3/
%dir %{pylibdir}/sqlite3/__pycache__/
%{pylibdir}/sqlite3/*.py
%{pylibdir}/sqlite3/__pycache__/*%{bytecode_suffixes}

%if %{without flatpackage}
%exclude %{pylibdir}/turtle.py
%exclude %{pylibdir}/__pycache__/turtle*%{bytecode_suffixes}
%endif

%{pylibdir}/urllib
%{pylibdir}/xml
%{pylibdir}/zoneinfo

%if "%{_lib}" == "lib64"
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages/__pycache__/
%endif

# "Makefile" and the config-32/64.h file are needed by
# distutils/sysconfig.py:_init_posix(), so we include them in the core
# package, along with their parent directories (bug 531901):
%dir %{pylibdir}/config-%{LDVERSION_optimized}-%{platform_triplet}/
%{pylibdir}/config-%{LDVERSION_optimized}-%{platform_triplet}/Makefile
%dir %{_includedir}/python%{LDVERSION_optimized}/
%{_includedir}/python%{LDVERSION_optimized}/%{_pyconfig_h}

%{_libdir}/%{py_INSTSONAME_optimized}
%if %{with main_python}
%{_libdir}/libpython3.so
%endif


%if %{without flatpackage}
%files -n %{pkgname}-devel
%endif

%if %{with main_python}
%{_bindir}/2to3
%endif

%{pylibdir}/config-%{LDVERSION_optimized}-%{platform_triplet}/*
%if %{without flatpackage}
%exclude %{pylibdir}/config-%{LDVERSION_optimized}-%{platform_triplet}/Makefile
%exclude %{_includedir}/python%{LDVERSION_optimized}/%{_pyconfig_h}
%endif
%{_includedir}/python%{LDVERSION_optimized}/*.h
%{_includedir}/python%{LDVERSION_optimized}/internal/
%{_includedir}/python%{LDVERSION_optimized}/cpython/
%doc Misc/README.valgrind Misc/valgrind-python.supp Misc/gdbinit

%if %{with main_python}
%{_bindir}/python3-config
%{_bindir}/python-config
%{_libdir}/pkgconfig/python3.pc
%{_libdir}/pkgconfig/python.pc
%{_libdir}/pkgconfig/python3-embed.pc
%{_bindir}/pathfix.py
%{_bindir}/pygettext3.py
%{_bindir}/pygettext.py
%{_bindir}/msgfmt3.py
%{_bindir}/msgfmt.py
%endif

%{_bindir}/pathfix%{pybasever}.py
%{_bindir}/pygettext%{pybasever}.py
%{_bindir}/msgfmt%{pybasever}.py

%{_bindir}/python%{pybasever}-config
%{_bindir}/python%{LDVERSION_optimized}-config
%{_bindir}/python%{LDVERSION_optimized}-*-config
%{_libdir}/libpython%{LDVERSION_optimized}.so
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}.pc
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}-embed.pc
%{_libdir}/pkgconfig/python-%{pybasever}.pc
%{_libdir}/pkgconfig/python-%{pybasever}-embed.pc

%if %{with rhel8_compat_shims}
%{_libexecdir}/platform-python-config
%{_libexecdir}/platform-python%{pybasever}-config
%{_libexecdir}/platform-python%{LDVERSION_optimized}-config
%{_libexecdir}/platform-python%{pybasever}-*-config
%{_libexecdir}/platform-python%{LDVERSION_optimized}-*-config
%endif


%if %{without flatpackage}
%files -n %{pkgname}-idle
%endif

%if %{with main_python}
%{_bindir}/idle*
%else
%{_bindir}/idle%{pybasever}
%endif

%{pylibdir}/idlelib

%if %{with main_python}
%{_metainfodir}/idle3.appdata.xml
%{_datadir}/applications/idle3.desktop
%{_datadir}/icons/hicolor/*/apps/idle3.*
%endif

%if %{without flatpackage}
%files -n %{pkgname}-tkinter
%endif

%{pylibdir}/tkinter
%if %{without flatpackage}
%exclude %{pylibdir}/tkinter/test
%endif
%{dynload_dir}/_tkinter.%{SOABI_optimized}.so
%{pylibdir}/turtle.py
%{pylibdir}/__pycache__/turtle*%{bytecode_suffixes}
%dir %{pylibdir}/turtledemo
%{pylibdir}/turtledemo/*.py
%{pylibdir}/turtledemo/*.cfg
%dir %{pylibdir}/turtledemo/__pycache__/
%{pylibdir}/turtledemo/__pycache__/*%{bytecode_suffixes}


%if %{without flatpackage}
%files -n %{pkgname}-test
%endif

%{pylibdir}/ctypes/test
%{pylibdir}/distutils/tests
%{pylibdir}/sqlite3/test
%{pylibdir}/test
%{dynload_dir}/_ctypes_test.%{SOABI_optimized}.so
%{dynload_dir}/_testbuffer.%{SOABI_optimized}.so
%{dynload_dir}/_testcapi.%{SOABI_optimized}.so
%{dynload_dir}/_testimportmultiple.%{SOABI_optimized}.so
%{dynload_dir}/_testinternalcapi.%{SOABI_optimized}.so
%{dynload_dir}/_testmultiphase.%{SOABI_optimized}.so
%{dynload_dir}/_xxtestfuzz.%{SOABI_optimized}.so
%{pylibdir}/lib2to3/tests
%{pylibdir}/tkinter/test
%{pylibdir}/unittest/test

# We don't bother splitting the debug build out into further subpackages:
# if you need it, you're probably a developer.

# Hence the manifest is the combination of analogous files in the manifests of
# all of the other subpackages

%if %{with debug_build}
%if %{without flatpackage}
%files -n %{pkgname}-debug
%endif

%if %{with main_python}
%{_bindir}/python3-debug
%{_bindir}/python-debug
%endif

# Analog of the core subpackage's files:
%{_bindir}/python%{LDVERSION_debug}

# Analog of the -libs subpackage's files:
# ...with debug builds of the built-in "extension" modules:

%{dynload_dir}/_blake2.%{SOABI_debug}.so
%{dynload_dir}/_md5.%{SOABI_debug}.so
%{dynload_dir}/_sha1.%{SOABI_debug}.so
%{dynload_dir}/_sha256.%{SOABI_debug}.so
%{dynload_dir}/_sha3.%{SOABI_debug}.so
%{dynload_dir}/_sha512.%{SOABI_debug}.so

%{dynload_dir}/_asyncio.%{SOABI_debug}.so
%{dynload_dir}/_bisect.%{SOABI_debug}.so
%{dynload_dir}/_bz2.%{SOABI_debug}.so
%{dynload_dir}/_codecs_cn.%{SOABI_debug}.so
%{dynload_dir}/_codecs_hk.%{SOABI_debug}.so
%{dynload_dir}/_codecs_iso2022.%{SOABI_debug}.so
%{dynload_dir}/_codecs_jp.%{SOABI_debug}.so
%{dynload_dir}/_codecs_kr.%{SOABI_debug}.so
%{dynload_dir}/_codecs_tw.%{SOABI_debug}.so
%{dynload_dir}/_contextvars.%{SOABI_debug}.so
%{dynload_dir}/_crypt.%{SOABI_debug}.so
%{dynload_dir}/_csv.%{SOABI_debug}.so
%{dynload_dir}/_ctypes.%{SOABI_debug}.so
%{dynload_dir}/_curses.%{SOABI_debug}.so
%{dynload_dir}/_curses_panel.%{SOABI_debug}.so
%{dynload_dir}/_dbm.%{SOABI_debug}.so
%{dynload_dir}/_decimal.%{SOABI_debug}.so
%{dynload_dir}/_elementtree.%{SOABI_debug}.so
%if %{with gdbm}
%{dynload_dir}/_gdbm.%{SOABI_debug}.so
%endif
%{dynload_dir}/_hashlib.%{SOABI_debug}.so
%{dynload_dir}/_heapq.%{SOABI_debug}.so
%{dynload_dir}/_json.%{SOABI_debug}.so
%{dynload_dir}/_lsprof.%{SOABI_debug}.so
%{dynload_dir}/_lzma.%{SOABI_debug}.so
%{dynload_dir}/_multibytecodec.%{SOABI_debug}.so
%{dynload_dir}/_multiprocessing.%{SOABI_debug}.so
%{dynload_dir}/_opcode.%{SOABI_debug}.so
%{dynload_dir}/_pickle.%{SOABI_debug}.so
%{dynload_dir}/_posixsubprocess.%{SOABI_debug}.so
%{dynload_dir}/_queue.%{SOABI_debug}.so
%{dynload_dir}/_random.%{SOABI_debug}.so
%{dynload_dir}/_socket.%{SOABI_debug}.so
%{dynload_dir}/_sqlite3.%{SOABI_debug}.so
%{dynload_dir}/_ssl.%{SOABI_debug}.so
%{dynload_dir}/_statistics.%{SOABI_debug}.so
%{dynload_dir}/_struct.%{SOABI_debug}.so
%{dynload_dir}/array.%{SOABI_debug}.so
%{dynload_dir}/audioop.%{SOABI_debug}.so
%{dynload_dir}/binascii.%{SOABI_debug}.so
%{dynload_dir}/cmath.%{SOABI_debug}.so
%{dynload_dir}/_datetime.%{SOABI_debug}.so
%{dynload_dir}/fcntl.%{SOABI_debug}.so
%{dynload_dir}/grp.%{SOABI_debug}.so
%{dynload_dir}/math.%{SOABI_debug}.so
%{dynload_dir}/mmap.%{SOABI_debug}.so
%{dynload_dir}/nis.%{SOABI_debug}.so
%{dynload_dir}/ossaudiodev.%{SOABI_debug}.so
%{dynload_dir}/parser.%{SOABI_debug}.so
%{dynload_dir}/_posixshmem.%{SOABI_debug}.so
%{dynload_dir}/pyexpat.%{SOABI_debug}.so
%{dynload_dir}/readline.%{SOABI_debug}.so
%{dynload_dir}/resource.%{SOABI_debug}.so
%{dynload_dir}/select.%{SOABI_debug}.so
%{dynload_dir}/spwd.%{SOABI_debug}.so
%{dynload_dir}/syslog.%{SOABI_debug}.so
%{dynload_dir}/termios.%{SOABI_debug}.so
%{dynload_dir}/unicodedata.%{SOABI_debug}.so
%{dynload_dir}/_uuid.%{SOABI_debug}.so
%{dynload_dir}/_xxsubinterpreters.%{SOABI_debug}.so
%{dynload_dir}/_xxtestfuzz.%{SOABI_debug}.so
%{dynload_dir}/zlib.%{SOABI_debug}.so
%{dynload_dir}/_zoneinfo.%{SOABI_debug}.so

# No need to split things out the "Makefile" and the config-32/64.h file as we
# do for the regular build above (bug 531901), since they're all in one package
# now; they're listed below, under "-devel":

%{_libdir}/%{py_INSTSONAME_debug}

# Analog of the -devel subpackage's files:
%{pylibdir}/config-%{LDVERSION_debug}-%{platform_triplet}
%{_includedir}/python%{LDVERSION_debug}
%{_bindir}/python%{LDVERSION_debug}-config
%{_bindir}/python%{LDVERSION_debug}-*-config
%{_libdir}/libpython%{LDVERSION_debug}.so
%{_libdir}/libpython%{LDVERSION_debug}.so.%{py_SOVERSION}
%{_libdir}/pkgconfig/python-%{LDVERSION_debug}.pc
%{_libdir}/pkgconfig/python-%{LDVERSION_debug}-embed.pc

%if %{with rhel8_compat_shims}
%{_libexecdir}/platform-python-debug
%{_libexecdir}/platform-python%{LDVERSION_debug}
%{_libexecdir}/platform-python%{LDVERSION_debug}-config
%{_libexecdir}/platform-python%{LDVERSION_debug}-*-config
%endif

# Analog of the -tools subpackage's files:
#  None for now; we could build precanned versions that have the appropriate
# shebang if needed

# Analog  of the tkinter subpackage's files:
%{dynload_dir}/_tkinter.%{SOABI_debug}.so

# Analog  of the -test subpackage's files:
%{dynload_dir}/_ctypes_test.%{SOABI_debug}.so
%{dynload_dir}/_testbuffer.%{SOABI_debug}.so
%{dynload_dir}/_testcapi.%{SOABI_debug}.so
%{dynload_dir}/_testimportmultiple.%{SOABI_debug}.so
%{dynload_dir}/_testinternalcapi.%{SOABI_debug}.so
%{dynload_dir}/_testmultiphase.%{SOABI_debug}.so

%endif # with debug_build

# We put the debug-gdb.py file inside /usr/lib/debug to avoid noise from ldconfig
# See https://bugzilla.redhat.com/show_bug.cgi?id=562980
#
# The /usr/lib/rpm/redhat/macros defines %%__debug_package to use
# debugfiles.list, and it appears that everything below /usr/lib/debug and
# (/usr/src/debug) gets added to this file (via LISTFILES) in
# /usr/lib/rpm/find-debuginfo.sh
#
# Hence by installing it below /usr/lib/debug we ensure it is added to the
# -debuginfo subpackage
# (if it doesn't, then the rpmbuild ought to fail since the debug-gdb.py
# payload file would be unpackaged)

# Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=1476593
%undefine _debuginfo_subpackages

# ======================================================
# Finally, the changelog:
# ======================================================

%changelog
* Thu May 05 2022 Antonio Ettorre <antonio@openquake.org> - 3.9.12-1
- First build of oq-python39 (migrated from oq-python38)
