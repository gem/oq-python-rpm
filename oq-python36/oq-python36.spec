# Override default installation
%define _prefix /opt/openquake
# docdir must be outside our prefix
%define _docdir /usr/share/doc

# ==================
# Top-level metadata
# ==================

%global pybasever 3.6

# pybasever without the dot:
%global pyshortver 36

Name: oq-python%{pyshortver}
Summary: Version %{pybasever} of the Python interpreter for OpenQuake
URL: https://www.python.org/

#  WARNING  When rebasing to a new Python version,
#           remember to update the python3-docs package as well
Version: %{pybasever}.6
Release: 1%{?dist}
License: Python


# ==================================
# Conditionals controlling the build
# ==================================

# Note that the bcond macros are named for the CLI option they create.
# "%%bcond_without" means "ENABLE by default and create a --without option"

# Expensive optimizations (mainly, profile-guided optimizations)
%ifarch %{ix86} x86_64
%bcond_without optimizations
%else
# On some architectures, the optimized build takes tens of hours, possibly
# longer than Koji's 24-hour timeout. Disable optimizations here.
%bcond_with optimizations
%endif

# Run the test suite in %%check
%bcond_with tests

# Main interpreter loop optimization
%bcond_without computed_gotos

# ==================================
# Notes from bootstraping Python 3.6
# ==================================
#
# New Python major version (3.X) break ABI and bytecode compatibility,
# so all packages depending on it need to be rebuilt.
#
# Due to a dependency cycle between Python, gdb, rpm, pip, setuptools, wheel,
# and other packages, this isn't straightforward.
# Build in the following order:
#
# 1. At the same time:
#     - gdb without python support (add %%global _without_python 1 on top of
#       gdb's SPEC file)
#     - python-rpm-generators
#       (this can be done also during step 2., but should be done before 3.)
# 2. python3 without rewheel (use %%bcond_with rewheel instead of
#     %%bcond_without)
# 3. gdb with python support (remove %%global _without_python 1 on top of
#    gdb's SPEC file)
# 4. rpm
# 5. python-setuptools with bootstrap set to 1
# 6. python-pip with build_wheel set to 0
# 7. python-wheel with %%bcond_without bootstrap
# 8. python-setuptools with bootstrap set to 0 and also with_check set to 0
# 9. python-pip with build_wheel set to 1
# 10. pyparsing
# 11. python3 with rewheel
#
# Then the most important packages have to be built, in dependency order.
# These were:
#   python-sphinx, pytest, python-requests, cloud-init, dnf, anaconda, abrt
#
# After these have been built, a targeted rebuild should be done for the rest.


# =====================
# General global macros
# =====================

%global pylibdir %{_libdir}/python%{pybasever}
%global dynload_dir %{pylibdir}/lib-dynload

# ABIFLAGS, LDVERSION and SOABI are in the upstream configure.ac
# See PEP 3149 for some background: http://www.python.org/dev/peps/pep-3149/
%global ABIFLAGS_optimized m

%global LDVERSION_optimized %{pybasever}%{ABIFLAGS_optimized}

%global SOABI_optimized cpython-%{pyshortver}%{ABIFLAGS_optimized}-%{_arch}-linux%{_gnu}

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

# Python's configure script defines SOVERSION, and this is used in the Makefile
# to determine INSTSONAME, the name of the libpython DSO:
#   LDLIBRARY='libpython$(VERSION).so'
#   INSTSONAME="$LDLIBRARY".$SOVERSION
# We mirror this here in order to make it easier to add the -gdb.py hooks.
# (if these get out of sync, the payload of the libs subpackage will fail
# and halt the build)
%global py_SOVERSION 1.0
%global py_INSTSONAME_optimized libpython%{LDVERSION_optimized}.so.%{py_SOVERSION}

# Make sure that the proper installation of python is used by macros
%define __python3 %{_bindir}/python3.5
%define __python %{__python3}

# Disable automatic bytecompilation. The python3 binary is not yet be
# available in /usr/bin when Python is built. Also, the bytecompilation fails
# on files that test invalid syntax.
%undefine py_auto_byte_compile

# Backported from EPEL:
#  https://src.fedoraproject.org/cgit/rpms/python36.git/tree/?h=epel7&id=ee1b6fe2f274b9a4b526263f42d208bbfbe08a2f
# We want to byte-compile the .py files within the packages using the new
# python3 binary.
#
# Unfortunately, rpmbuild's infrastructure requires us to jump through some
# hoops to avoid byte-compiling with the system python version:
#   /usr/lib/rpm/redhat/macros sets up build policy that (amongst other things)
# defines __os_install_post.  In particular, "brp-python-bytecompile" is
# invoked without an argument thus using the wrong version of python3
# (/usr/bin/python3.6, rather than the freshly built python3), thus leading to
# numerous syntax errors, and incorrect magic numbers in the .pyc files.  We
# thus override __os_install_post to avoid invoking this script:
%global __os_install_post /usr/lib/rpm/brp-compress \
  %{!?__debug_package:/usr/lib/rpm/brp-strip %{__strip}} \
  /usr/lib/rpm/brp-strip-static-archive %{__strip} \
  /usr/lib/rpm/brp-strip-comment-note %{__strip} %{__objdump} \
  /usr/lib/rpm/brp-python-hardlink
# to remove the invocation of brp-python-bytecompile, whilst keeping the
# invocation of brp-python-hardlink (since this should still work for python3
# pyc files)

# For multilib support, files that are different between 32- and 64-bit arches
# need different filenames. Use "64" or "32" according to the word size.
# Currently, the best way to determine an architecture's word size happens to
# be checking %%{_lib}.
%if "%{_lib}" == "lib64"
%global wordsize 64
%else
%global wordsize 32
%endif


# =======================
# Build-time requirements
# =======================

# (keep this list alphabetized)

BuildRequires: autoconf
BuildRequires: bluez-libs-devel
BuildRequires: bzip2
BuildRequires: bzip2-devel
BuildRequires: expat-devel

BuildRequires: findutils
BuildRequires: gcc-c++
BuildRequires: glibc-devel
BuildRequires: gmp-devel
BuildRequires: libappstream-glib
BuildRequires: libffi-devel
%if 0%{?fedora} >= 27
BuildRequires: libnsl2-devel
%endif
BuildRequires: libtirpc-devel
BuildRequires: libGL-devel
BuildRequires: libX11-devel
BuildRequires: ncurses-devel

BuildRequires: openssl-devel
BuildRequires: pkgconfig
BuildRequires: readline-devel
BuildRequires: sqlite-devel

BuildRequires: tar
BuildRequires: tcl-devel
BuildRequires: tix-devel
BuildRequires: tk-devel

BuildRequires: xz-devel
BuildRequires: zlib-devel

BuildRequires: /usr/bin/dtrace

# workaround http://bugs.python.org/issue19804 (test_uuid requires ifconfig)
%if 0%{?fedora}
BuildRequires: /usr/sbin/ifconfig
%else
BuildRequires: /sbin/ifconfig
%endif


# =======================
# Source code and patches
# =======================

Source: https://www.python.org/ftp/python/%{version}/Python-%{version}.tar.xz

# A simple script to check timestamps of bytecode files
# Run in check section with Python that is currently being built
# Written by bkabrda
Source8: check-pyc-and-pyo-timestamps.py

# 00001 #
# Fixup distutils/unixccompiler.py to remove standard library path from rpath:
# Was Patch0 in ivazquez' python3000 specfile:
Patch1:         00001-rpath.patch

# 00102 #
# Change the various install paths to use /usr/lib64/ instead or /usr/lib
# Only used when "%%{_lib}" == "lib64"
# Not yet sent upstream.
Patch102: 00102-lib64.patch

# 00132 #
# Add non-standard hooks to unittest for use in the "check" phase below, when
# running selftests within the build:
#   @unittest._skipInRpmBuild(reason)
# for tests that hang or fail intermittently within the build environment, and:
#   @unittest._expectedFailureInRpmBuild
# for tests that always fail within the build environment
#
# The hooks only take effect if WITHIN_PYTHON_RPM_BUILD is set in the
# environment, which we set manually in the appropriate portion of the "check"
# phase below (and which potentially other python-* rpms could set, to reuse
# these unittest hooks in their own "check" phases)
Patch132: 00132-add-rpmbuild-hooks-to-unittest.patch

# 00155 #
# Avoid allocating thunks in ctypes unless absolutely necessary, to avoid
# generating SELinux denials on "import ctypes" and "import uuid" when
# embedding Python within httpd
# See https://bugzilla.redhat.com/show_bug.cgi?id=814391
Patch155: 00155-avoid-ctypes-thunks.patch

# 00160 #
# Python 3.3 added os.SEEK_DATA and os.SEEK_HOLE, which may be present in the
# header files in the build chroot, but may not be supported in the running
# kernel, hence we disable this test in an rpm build.
# Adding these was upstream issue http://bugs.python.org/issue10142
# Not yet sent upstream
Patch160: 00160-disable-test_fs_holes-in-rpm-build.patch

# 00163 #
# Some tests within test_socket fail intermittently when run inside Koji;
# disable them using unittest._skipInRpmBuild
# Not yet sent upstream
Patch163: 00163-disable-parts-of-test_socket-in-rpm-build.patch

# 00170 #
# In debug builds, try to print repr() when a C-level assert fails in the
# garbage collector (typically indicating a reference-counting error
# somewhere else e.g in an extension module)
# The new macros/functions within gcmodule.c are hidden to avoid exposing
# them within the extension API.
# Sent upstream: http://bugs.python.org/issue9263
# See https://bugzilla.redhat.com/show_bug.cgi?id=614680
Patch170: 00170-gc-assertions.patch

# 00178 #
# Don't duplicate various FLAGS in sysconfig values
# http://bugs.python.org/issue17679
# Does not affect python2 AFAICS (different sysconfig values initialization)
Patch178: 00178-dont-duplicate-flags-in-sysconfig.patch

# 00205 #
# LIBPL variable in makefile takes LIBPL from configure.ac
# but the LIBPL variable defined there doesn't respect libdir macro
Patch205: 00205-make-libpl-respect-lib64.patch

# 00262 #
# Backport of PEP 538: Coercing the legacy C locale to a UTF-8 based locale
# https://www.python.org/dev/peps/pep-0538/
# Fedora Change: https://fedoraproject.org/wiki/Changes/python3_c.utf-8_locale
# Original proposal: https://bugzilla.redhat.com/show_bug.cgi?id=1404918
Patch262: 00262-pep538_coerce_legacy_c_locale.patch

# 00274 #
# Upstream uses Debian-style architecture naming. Change to match Fedora.
Patch274: 00274-fix-arch-names.patch

# 00292 #
# Restore the public PyExc_RecursionErrorInst symbol that was removed
# from the 3.6.4 release upstream.
# Reported upstream: https://bugs.python.org/issue30697
Patch292: 00292-restore-PyExc_RecursionErrorInst-symbol.patch

# 00294 #
# Define TLS cipher suite on build time depending
# on the OpenSSL default cipher suite selection.
# Fixed upstream on CPython's 3.7 branch:
# https://bugs.python.org/issue31429
# See also: https://bugzilla.redhat.com/show_bug.cgi?id=1489816
Patch294: 00294-define-TLS-cipher-suite-on-build-time.patch

# (New patches go here ^^^)
#
# When adding new patches to "python" and "python3" in Fedora, EL, etc.,
# please try to keep the patch numbers in-sync between all specfiles.
#
# More information, and a patch number catalog, is at:
#
#     https://fedoraproject.org/wiki/SIGs/Python/PythonPatches


# ==========================================
# Descriptions, and metadata for subpackages
# ==========================================

# We'll not provide this, on purpose
# No package in Fedora shall ever depend on flatpackage via this
%global __requires_exclude ^python\\(abi\\) = 3\\..$
%global __provides_exclude ^python\\(abi\\) = 3\\..$

Provides: oq-python3
Obsoletes: oq-python35

%description
Python %{pybasever} package for OpenQuake

# ======================================================
# The prep phase of the build:
# ======================================================

%prep
%setup -q -n Python-%{version}%{?prerel}

# Remove bundled libraries to ensure that we're using the system copy.
rm -r Modules/expat
rm -r Modules/zlib

#
# Apply patches:
#
%patch1 -p1

%if "%{_lib}" == "lib64"
%patch102 -p1
%endif
%patch132 -p1
%patch155 -p1
%patch160 -p1
%patch163 -p1
%patch170 -p1
%patch178 -p1

%patch205 -p1
%patch262 -p1
%patch274 -p1
%patch292 -p1
%patch294 -p1


# Remove files that should be generated by the build
# (This is after patching, so that we can use patches directly from upstream)
rm configure pyconfig.h.in


# ======================================================
# Configuring and building the code:
# ======================================================

%build

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
export CFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export CXXFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export CPPFLAGS="$(pkg-config --cflags-only-I libffi)"
export OPT="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export LINKCC="gcc"
export CFLAGS="$CFLAGS $(pkg-config --cflags openssl)"
export LDFLAGS="$RPM_LD_FLAGS -g $(pkg-config --libs-only-L openssl)"

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

%configure \
  --enable-ipv6 \
  --with-computed-gotos=%{computed_gotos_flag} \
  --with-system-expat \
  --with-system-ffi \
  --enable-loadable-sqlite-extensions \
  --with-dtrace \
%if 0%{?fedora}
  --with-lto \
%endif
  --with-ssl-default-suites=openssl \
  $ExtraConfigArgs \
  %{nil}

  # Invoke the build
  make EXTRA_CFLAGS="$CFLAGS $MoreCFlags" %{?_smp_mflags}

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
%global _pyconfig_h pyconfig-%{wordsize}.h

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

  make \
    DESTDIR=%{buildroot} \
    INSTALL="install -p" \
    EXTRA_CFLAGS="$MoreCFlags" \
    install

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
# cp -p Tools/scripts/pathfix.py %{buildroot}%{_bindir}/

# Switch all shebangs to refer to the specific Python version.
# This currently only covers files matching ^[a-zA-Z0-9_]+\.py$,
# so handle files named using other naming scheme separately.
LD_LIBRARY_PATH=./build/optimized ./build/optimized/python \
  Tools/scripts/pathfix.py \
  -i "%{_bindir}/python%{pybasever}" -pn \
  %{buildroot}

# Remove tests for python3-tools which was removed in
# https://bugzilla.redhat.com/show_bug.cgi?id=1312030
rm -rf %{buildroot}%{pylibdir}/test/test_tools

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

# Get rid of a stray copy of the license:
rm %{buildroot}%{pylibdir}/LICENSE.txt

# Do bytecompilation with the newly installed interpreter.
# This is similar to the script in macros.pybytecompile
# compile *.pyc
find %{buildroot} -type f -a -name "*.py" -print0 | \
    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} -O -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("%{buildroot}")[2], optimize=opt) for opt in range(3) for f in sys.argv[1:]]' || :

# Since we have pathfix.py in bindir, this is created, but we don't want it
rm -rf %{buildroot}%{_bindir}/__pycache__

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find %{buildroot} -perm 555 -exec chmod 755 {} \;

# ======================================================
# Checks for packaging issues
# ======================================================

%check

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

  # Run the upstream test suite, setting "WITHIN_PYTHON_RPM_BUILD" so that the
  # our non-standard decorators take effect on the relevant tests:
  #   @unittest._skipInRpmBuild(reason)
  #   @unittest._expectedFailureInRpmBuild
  # test_faulthandler.test_register_chain currently fails on ppc64le and
  #   aarch64, see upstream bug http://bugs.python.org/issue21131
  WITHIN_PYTHON_RPM_BUILD= \
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.regrtest \
    -wW --slowest --findleaks \
    -x test_distutils \
    -x test_bdist_rpm \
    %ifarch ppc64le aarch64
    -x test_faulthandler \
    %endif
    %ifarch %{mips64}
    -x test_ctypes \
    %endif
    %ifarch ppc64le
    -x test_buffer \
    %endif

  echo FINISHED: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

}

%if %{with tests}

# Check each of the configurations:
CheckPython optimized

%endif # with tests


# ======================================================
# Scriptlets
# ======================================================

# Convert lib64 symlink into a real dir to avoid transaction conflicts during upgrades.
# See: https://fedoraproject.org/wiki/Packaging:Directory_Replacement#Scriptlet_to_replace_a_symlink_to_a_directory_with_a_directory
%pretrans -p <lua>
path = "%{_libdir}"
st = posix.stat(path)
if st and st.type == "link" then
  os.remove(path)
end

%files
%doc README.rst LICENSE

# In /opt/openquake we are the owners of bin, usr and so on
%dir %{_prefix}
%dir %{_bindir}
%dir %{_libdir}
%if "%{_lib}" == "lib64"
%dir %{_prefix}/lib
%endif
%dir %{_includedir}
%dir %{_datadir}

%{_bindir}/pydoc3
%{_bindir}/python3
%{_bindir}/pyvenv
%{_bindir}/pip3

%{_bindir}/pydoc%{pybasever}
%{_bindir}/python%{pybasever}
%{_bindir}/python%{pybasever}m
%{_bindir}/pyvenv-%{pybasever}
%{_bindir}/pip%{pybasever}
%{_bindir}/easy_install-%{pybasever}
%{_mandir}

%{pylibdir}/

%if "%{_lib}" == "lib64"
%{_prefix}/lib/python%{pybasever}
%endif

%{_includedir}/python%{LDVERSION_optimized}/

%{_bindir}/python3-config
%{_bindir}/python%{pybasever}-config
%{_bindir}/python%{LDVERSION_optimized}-config
%{_bindir}/python%{LDVERSION_optimized}-*-config
%{_libdir}/libpython%{LDVERSION_optimized}.a
%dir %{_libdir}/pkgconfig
%{_libdir}/pkgconfig/python3.pc
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}.pc
%{_libdir}/pkgconfig/python-%{pybasever}.pc


%{_bindir}/2to3
%{_bindir}/2to3-%{pybasever}
%{_bindir}/idle3
%{_bindir}/idle%{pybasever}

# Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=1476593
%undefine _debuginfo_subpackages

# ======================================================
# Finally, the changelog:
# ======================================================

%changelog
* Mon Jul 16 2018 Daniele Viganò <daniele@vigano.me> - 3.6.6-1
- First build of oq-python36 (migrated from oq-python35)
