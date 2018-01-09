# ======================================================
# Conditionals and other variables controlling the build
# ======================================================

%global pybasever 3.5

# pybasever without the dot:
%global pyshortver 35

%global pylibdir %{_libdir}/python%{pybasever}
%global dynload_dir %{pylibdir}/lib-dynload

# SOABI is defined in the upstream configure.in from Python-3.2a2 onwards,
# for PEP 3149:
#   http://www.python.org/dev/peps/pep-3149/

# ("configure.in" became "configure.ac" in Python 3.3 onwards, and in
# backports)

# ABIFLAGS, LDVERSION and SOABI are in the upstream Makefile
# With Python 3.3, we lose the "u" suffix due to PEP 393
%global ABIFLAGS_optimized m
%global ABIFLAGS_debug     dm

%global LDVERSION_optimized %{pybasever}%{ABIFLAGS_optimized}
%global LDVERSION_debug     %{pybasever}%{ABIFLAGS_debug}

%global SOABI_optimized cpython-%{pyshortver}%{ABIFLAGS_optimized}-%{_arch}-linux%{_gnu}
%global SOABI_debug     cpython-%{pyshortver}%{ABIFLAGS_debug}-%{_arch}-linux%{_gnu}

# All bytecode files are now in a __pycache__ subdirectory, with a name
# reflecting the version of the bytecode (to permit sharing of python libraries
# between different runtimes)
# See http://www.python.org/dev/peps/pep-3147/
# For example,
#   foo/bar.py
# now has bytecode at:
#   foo/__pycache__/bar.cpython-35.pyc
#   foo/__pycache__/bar.cpython-35.pyo
%global bytecode_suffixes .cpython-35*.py?

# Python's configure script defines SOVERSION, and this is used in the Makefile
# to determine INSTSONAME, the name of the libpython DSO:
#   LDLIBRARY='libpython$(VERSION).so'
#   INSTSONAME="$LDLIBRARY".$SOVERSION
# We mirror this here in order to make it easier to add the -gdb.py hooks.
# (if these get out of sync, the payload of the libs subpackage will fail
# and halt the build)
%global py_SOVERSION 1.0
%global py_INSTSONAME_optimized libpython%{LDVERSION_optimized}.so.%{py_SOVERSION}
%global py_INSTSONAME_debug     libpython%{LDVERSION_debug}.so.%{py_SOVERSION}

%global with_debug_build 0

%global with_gdb_hooks 1

%global with_systemtap 1

# some arches don't have valgrind so we need to disable its support on them
%ifnarch s390 %{mips}
%global with_valgrind 1
%else
%global with_valgrind 0
%endif

%global with_gdbm 1

# Change from yes to no to turn this off
%global with_computed_gotos yes

# Turn this to 0 to turn off the "check" phase:
%global run_selftest_suite 1

# We want to byte-compile the .py files within the packages using the new
# python3 binary.
#
# Unfortunately, rpmbuild's infrastructure requires us to jump through some
# hoops to avoid byte-compiling with the system python 2 version:
#   /usr/lib/rpm/redhat/macros sets up build policy that (amongst other things)
# defines __os_install_post.  In particular, "brp-python-bytecompile" is
# invoked without an argument thus using the wrong version of python
# (/usr/bin/python, rather than the freshly built python), thus leading to
# numerous syntax errors, and incorrect magic numbers in the .pyc files.  We
# thus override __os_install_post to avoid invoking this script:
%global __os_install_post /usr/lib/rpm/brp-compress \
  %{!?__debug_package:/usr/lib/rpm/brp-strip %{__strip}} \
  /usr/lib/rpm/brp-strip-static-archive %{__strip} \
  /usr/lib/rpm/brp-strip-comment-note %{__strip} %{__objdump} \
  /usr/lib/rpm/brp-python-hardlink
# to remove the invocation of brp-python-bytecompile, whilst keeping the
# invocation of brp-python-hardlink (since this should still work for python3
# pyc/pyo files)


# ==================
# Top-level metadata
# ==================
Summary: Version 3.5 of the Python programming language
Name: python%{pyshortver}
Version: %{pybasever}.4
Release: 2%{?dist}
License: Python
Group: Development/Languages


# =======================
# Build-time requirements
# =======================

# (keep this list alphabetized)

BuildRequires: autoconf
BuildRequires: bluez-libs-devel
BuildRequires: bzip2
BuildRequires: bzip2-devel

# expat 2.1.0 added the symbol XML_SetHashSalt without bumping SONAME.  We use
# it (in pyexpat) in order to enable the fix in Python-3.2.3 for CVE-2012-0876:
BuildRequires: expat-devel >= 2.1.0

BuildRequires: findutils
BuildRequires: gcc-c++
%if %{with_gdbm}
BuildRequires: gdbm-devel
%endif
BuildRequires: glibc-devel
BuildRequires: gmp-devel
BuildRequires: libffi-devel
BuildRequires: libGL-devel
BuildRequires: libX11-devel
BuildRequires: ncurses-devel
# workaround http://bugs.python.org/issue19804 (test_uuid requires ifconfig)
BuildRequires: net-tools
BuildRequires: openssl-devel
BuildRequires: pkgconfig
BuildRequires: readline-devel
BuildRequires: sqlite-devel

%if 0%{?with_systemtap}
BuildRequires: systemtap-sdt-devel
# (this introduces a dependency on "python", in that systemtap-sdt-devel's
# /usr/bin/dtrace is a python 2 script)
%global tapsetdir      /usr/share/systemtap/tapset
%endif # with_systemtap

BuildRequires: tar
BuildRequires: tcl-devel
BuildRequires: tix-devel
BuildRequires: tk-devel

%if 0%{?with_valgrind}
BuildRequires: valgrind-devel
%endif

BuildRequires: xz-devel
BuildRequires: zlib-devel

Requires:      expat >= 2.1.0

# Python 3 built with glibc >= 2.24.90-26 needs to require it (rhbz#1410644).
Requires: glibc%{?_isa} >= 2.24.90-26

BuildRequires: python-rpm-macros

# =======================
# Source code and patches
# =======================

Source: http://www.python.org/ftp/python/%{version}/Python-%{version}.tar.xz

# Supply an RPM macro "py_byte_compile" for the python3-devel subpackage
# to enable specfiles to selectively byte-compile individual files and paths
# with different Python runtimes as necessary:
Source3: macros.pybytecompile%{pybasever}

# Systemtap tapset to make it easier to use the systemtap static probes
# (actually a template; LIBRARY_PATH will get fixed up during install)
# Written by dmalcolm; not yet sent upstream
Source5: libpython.stp

# Example systemtap script using the tapset
# Written by wcohen, mjw, dmalcolm; not yet sent upstream
Source6: systemtap-example.stp

# Another example systemtap script that uses the tapset
# Written by dmalcolm; not yet sent upstream
Source7: pyfuntop.stp

# A simple script to check timestamps of bytecode files
# Run in check section with Python that is currently being built
# Written by bkabrda
Source8: check-pyc-and-pyo-timestamps.py

# Fixup distutils/unixccompiler.py to remove standard library path from rpath:
# Was Patch0 in ivazquez' python3000 specfile:
Patch1:         Python-3.1.1-rpath.patch

# 00055 #
# Systemtap support: add statically-defined probe points
# Patch sent upstream as http://bugs.python.org/issue14776
# with some subsequent reworking to cope with LANG=C in an rpmbuild
# (where sys.getfilesystemencoding() == 'ascii')
Patch55: 00055-systemtap.patch

Patch102: 00102-lib64.patch

# 00104 #
# Only used when "%{_lib}" == "lib64"
# Another lib64 fix, for distutils/tests/test_install.py; not upstream:
Patch104: 00104-lib64-fix-for-test_install.patch

# 00111 #
# Patch the Makefile.pre.in so that the generated Makefile doesn't try to build
# a libpythonMAJOR.MINOR.a (bug 550692):
# Downstream only: not appropriate for upstream
Patch111: 00111-no-static-lib.patch

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

# 00133 #
# 00133-skip-test_dl.patch is not relevant for python3: the "dl" module no
# longer exists

# 00137 #
# Some tests within distutils fail when run in an rpmbuild:
Patch137: 00137-skip-distutils-tests-that-fail-in-rpmbuild.patch

# 00143 #
# Fix the --with-tsc option on ppc64, and rework it on 32-bit ppc to avoid
# aliasing violations (rhbz#698726)
# Sent upstream as http://bugs.python.org/issue12872
Patch143: 00143-tsc-on-ppc.patch

# 00146 #
# Support OpenSSL FIPS mode (e.g. when OPENSSL_FORCE_FIPS_MODE=1 is set)
# - handle failures from OpenSSL (e.g. on attempts to use MD5 in a
#   FIPS-enforcing environment)
# - add a new "usedforsecurity" keyword argument to the various digest
#   algorithms in hashlib so that you can whitelist a callsite with
#   "usedforsecurity=False"
# (sent upstream for python 3 as http://bugs.python.org/issue9216 ; see RHEL6
# python patch 119)
# - enforce usage of the _hashlib implementation: don't fall back to the _md5
#   and _sha* modules (leading to clearer error messages if fips selftests
#   fail)
# - don't build the _md5 and _sha* modules; rely on the _hashlib implementation
#   of hashlib
# (rhbz#563986)
# Note: Up to Python 3.4.0.b1, upstream had their own implementation of what
# they assumed would become sha3. This patch was adapted to give it the
# usedforsecurity argument, even though it did nothing (OpenSSL didn't have
# sha3 implementation at that time).In 3.4.0.b2, sha3 implementation was reverted
# (see http://bugs.python.org/issue16113), but the alterations were left in the
# patch, since they may be useful again if upstream decides to rerevert sha3
# implementation and OpenSSL still doesn't support it. For now, they're harmless.
Patch146: 00146-hashlib-fips.patch

# 00155 #
# Avoid allocating thunks in ctypes unless absolutely necessary, to avoid
# generating SELinux denials on "import ctypes" and "import uuid" when
# embedding Python within httpd (rhbz#814391)
Patch155: 00155-avoid-ctypes-thunks.patch

# 00157 #
# Update uid/gid handling throughout the standard library: uid_t and gid_t are
# unsigned 32-bit values, but existing code often passed them through C long
# values, which are signed 32-bit values on 32-bit architectures, leading to
# negative int objects for uid/gid values >= 2^31 on 32-bit architectures.
#
# Introduce _PyObject_FromUid/Gid to convert uid_t/gid_t values to python
# objects, using int objects where the value will fit (long objects otherwise),
# and _PyArg_ParseUid/Gid to convert int/long to uid_t/gid_t, with -1 allowed
# as a special case (since this is given special meaning by the chown syscall)
#
# Update standard library to use this throughout for uid/gid values, so that
# very large uid/gid values are round-trippable, and -1 remains usable.
# (rhbz#697470)
Patch157: 00157-uid-gid-overflows.patch

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
# Backported to 2.7 from a patch I sent upstream for py3k
#   http://bugs.python.org/issue9263  (rhbz#614680)
# hiding the proposed new macros/functions within gcmodule.c to avoid exposing
# them within the extension API.
# (rhbz#850013
Patch170: 00170-gc-assertions.patch

# 00178 #
# Don't duplicate various FLAGS in sysconfig values
# http://bugs.python.org/issue17679
# Does not affect python2 AFAICS (different sysconfig values initialization)
Patch178: 00178-dont-duplicate-flags-in-sysconfig.patch

# 00180 #
# Enable building on ppc64p7
# Not appropriate for upstream, Fedora-specific naming
Patch180: 00180-python-add-support-for-ppc64p7.patch

# 00186 #
# Fix for https://bugzilla.redhat.com/show_bug.cgi?id=1023607
# Previously, this fixed a problem where some *.py files were not being
# bytecompiled properly during build. This was result of py_compile.compile
# raising exception when trying to convert test file with bad encoding, and
# thus not continuing bytecompilation for other files.
# This was fixed upstream, but the test hasn't been merged yet, so we keep it
Patch186: 00186-dont-raise-from-py_compile.patch

# 00188 #
# Downstream only patch that should be removed when we compile all guaranteed
# hashlib algorithms properly. The problem is this:
# - during tests, test_hashlib is imported and executed before test_lib2to3
# - if at least one hash function has failed, trying to import it triggers an
#   exception that is being caught and exception is logged:
#   http://hg.python.org/cpython/file/2de806c8b070/Lib/hashlib.py#l217
# - logging the exception makes logging module run basicConfig
# - when lib2to3 tests are run again, lib2to3 runs basicConfig again, which
#   doesn't do anything, because it was run previously
#   (logging.root.handlers != []), which means that the default setup
#   (most importantly logging level) is not overriden. That means that a test
#   relying on this will fail (test_filename_changing_on_output_single_dir)
Patch188: 00188-fix-lib2to3-tests-when-hashlib-doesnt-compile-properly.patch

# 00205 #
# LIBPL variable in makefile takes LIBPL from configure.ac
# but the LIBPL variable defined there doesn't respect libdir macro
Patch205: 00205-make-libpl-respect-lib64.patch

# 00206 #
# Remove hf flag from arm triplet which is used
# by debian but fedora infra uses only eabi without hf
Patch206: 00206-remove-hf-from-arm-triplet.patch

# 00243 #
# Fix the triplet used on 64-bit MIPS
# rhbz#1322526: https://bugzilla.redhat.com/show_bug.cgi?id=1322526
# Upstream uses Debian-like style mips64-linux-gnuabi64
# Fedora needs the default mips64-linux-gnu
Patch243: 00243-fix-mips64-triplet.patch

# 00264 #
# test_pass_by_value was added in Python 3.5.4 and on aarch64
# it is catching an error that was there, but wasn't tested before.
# Since the Python 3.5 branch is on security bug fix mode only
# we backport the fix from the master branch.
# Fixed upstream: http://bugs.python.org/issue29804
Patch264: 00264-fix-test-failing-on-aarch64.patch

# 00270 #
# Fix test_alpn_protocols from test_ssl as openssl > 1.1.0f
# changed the behaviour of the ALPN hook.
# Fixed upstream: http://bugs.python.org/issue30714
Patch270: 00270-fix-ssl-alpn-hook-test.patch

# 00273 #
# Skip test_float_with_comma, which fails in Koji with UnicodeDecodeError
# See https://bugzilla.redhat.com/show_bug.cgi?id=1484497
# Reported upstream: https://bugs.python.org/issue31900
Patch273: 00273-skip-float-test.patch

# 00286 #
# CVE-2017-1000158
# Check & prevent integer overflow in PyString_DecodeEscape
# Fixed upstream: https://bugs.python.org/issue30657
Patch286: 00286-pystring-decodeescape-integer-overflow.patch

# (New patches go here ^^^)
#
# When adding new patches to "python" and "python3" in Fedora, EL, etc.,
# please try to keep the patch numbers in-sync between all specfiles.
#
# More information, and a patch number catalog, is at:
#
#     https://fedoraproject.org/wiki/SIGs/Python/PythonPatches


# add correct arch for ppc64/ppc64le
# it should be ppc64le-linux-gnu/ppc64-linux-gnu instead powerpc64le-linux-gnu/powerpc64-linux-gnu
Patch5001: python3-powerppc-arch.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-root

# ======================================================
# Additional metadata, and subpackages
# ======================================================

URL: http://www.python.org/

# We'll not provide this, on purpose
# No package in Fedora shall ever depend on this
# Provides: python(abi) = %{pybasever}
%global __requires_exclude ^python\\(abi\\) = 3\\..$
%global __provides_exclude ^python\\(abi\\) = 3\\..$

# We keep those inside on purpose
Provides: bundled(python3-pip) = 8.1.1
Provides: bundled(python3-setuptools) = 20.10.1

%description
Python %{pybasever} package for developers.

This package exists to allow developers to test their code against an older
version of Python. This is not a full Python stack and if you wish to run
your applications with Python %{pybasever}, see other distributions
that support it, such as CentOS or RHEL with Software Collections
or older Fedora releases.


# ======================================================
# The prep phase of the build:
# ======================================================

%prep
%setup -q -n Python-%{version}%{?prerel}

%if 0%{?with_systemtap}
# Provide an example of usage of the tapset:
cp -a %{SOURCE6} .
cp -a %{SOURCE7} .
%endif # with_systemtap

# Ensure that we're using the system copy of various libraries, rather than
# copies shipped by upstream in the tarball:
#   Remove embedded copy of expat:
rm -r Modules/expat || exit 1

#   Remove embedded copy of libffi:
for SUBDIR in darwin libffi libffi_arm_wince libffi_msvc libffi_osx ; do
  rm -r Modules/_ctypes/$SUBDIR || exit 1 ;
done

#   Remove embedded copy of zlib:
rm -r Modules/zlib || exit 1

## Disabling hashlib patch for now as it needs to be reimplemented
## for OpenSSL 1.1.0.
# Don't build upstream Python's implementation of these crypto algorithms;
# instead rely on _hashlib and OpenSSL.
#
# For example, in our builds hashlib.md5 is implemented within _hashlib via
# OpenSSL (and thus respects FIPS mode), and does not fall back to _md5
# TODO: there seems to be no OpenSSL support in Python for sha3 so far
# when it is there, also remove _sha3/ dir
#for f in md5module.c sha1module.c sha256module.c sha512module.c; do
#    rm Modules/$f
#done

#
# Apply patches:
#
%patch1 -p1

%if 0%{?with_systemtap}
%patch55 -p1 -b .systemtap
%endif

%if "%{_lib}" == "lib64"
%patch102 -p1
%patch104 -p1
%endif
%patch111 -p1
%patch132 -p1
%patch137 -p1
%patch143 -p1 -b .tsc-on-ppc
#patch146 -p1
%patch155 -p1
%patch157 -p1
%patch160 -p1
%patch163 -p1
%patch170 -p0
%patch178 -p1
%patch180 -p1
%patch186 -p1
%patch188 -p1
%patch205 -p1
%patch206 -p1
%patch243 -p1
%patch264 -p1
%patch270 -p1
%patch273 -p1
%patch286 -p1

# Currently (2010-01-15), http://docs.python.org/library is for 2.6, and there
# are many differences between 2.6 and the Python 3 library.
#
# Fix up the URLs within pydoc to point at the documentation for this
# MAJOR.MINOR version:
#
sed --in-place \
    --expression="s|http://docs.python.org/library|http://docs.python.org/%{pybasever}/library|g" \
    Lib/pydoc.py || exit 1

%patch5001 -p1

# ======================================================
# Configuring and building the code:
# ======================================================

%build
topdir=$(pwd)
export CFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export CXXFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export CPPFLAGS="`pkg-config --cflags-only-I libffi`"
export OPT="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export LINKCC="gcc"
export CFLAGS="$CFLAGS `pkg-config --cflags openssl`"
export LDFLAGS="$RPM_LD_FLAGS `pkg-config --libs-only-L openssl`"


# Define a function, for how to perform a "build" of python for a given
# configuration:
BuildPython() {
  ConfName=$1
  BinaryName=$2
  SymlinkName=$3
  ExtraConfigArgs=$4
  PathFixWithThisBinary=$5
  MoreCFlags=$6

  ConfDir=build/$ConfName

  echo STARTING: BUILD OF PYTHON FOR CONFIGURATION: $ConfName - %{_bindir}/$BinaryName
  mkdir -p $ConfDir

  pushd $ConfDir

  # Use the freshly created "configure" script, but in the directory two above:
  %global _configure $topdir/configure

%configure \
  --enable-ipv6 \
  --enable-shared \
  --with-computed-gotos=%{with_computed_gotos} \
  --with-dbmliborder=gdbm:ndbm:bdb \
  --with-system-expat \
  --with-system-ffi \
  --enable-loadable-sqlite-extensions \
%if 0%{?with_systemtap}
  --with-systemtap \
%endif
%if 0%{?with_valgrind}
  --with-valgrind \
%endif
  $ExtraConfigArgs \
  %{nil}

  # Set EXTRA_CFLAGS to our CFLAGS (rather than overriding OPT, as we've done
  # in the past).
  # This should fix a problem with --with-valgrind where it adds
  #   -DDYNAMIC_ANNOTATIONS_ENABLED=1
  # to OPT which must be passed to all compilation units in the build,
  # otherwise leading to linker errors, e.g.
  #    missing symbol AnnotateRWLockDestroy
  #
  # Invoke the build:
  make EXTRA_CFLAGS="$CFLAGS $MoreCFlags" %{?_smp_mflags}

  popd
  echo FINISHED: BUILD OF PYTHON FOR CONFIGURATION: $ConfDir
}

# Use "BuildPython" to support building with different configurations:

%if 0%{?with_debug_build}
BuildPython debug \
  python-debug \
  python%{pybasever}-debug \
%ifarch %{ix86} x86_64 ppc %{power64}
  "--with-pydebug --with-tsc --without-ensurepip" \
%else
  "--with-pydebug --without-ensurepip" \
%endif
  false \
  -O0
%endif # with_debug_build

BuildPython optimized \
  python \
  python%{pybasever} \
%ifarch %{ix86} x86_64
  "--without-ensurepip --enable-optimizations" \
%else
   "--without-ensurepip" \
%endif
  true

# ======================================================
# Installing the built code:
# ======================================================

%install
topdir=$(pwd)
rm -fr %{buildroot}
mkdir -p %{buildroot}%{_prefix} %{buildroot}%{_mandir}

InstallPython() {

  ConfName=$1
  PyInstSoName=$2
  MoreCFlags=$3

  ConfDir=build/$ConfName

  echo STARTING: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
  mkdir -p $ConfDir

  pushd $ConfDir

make install DESTDIR=%{buildroot} INSTALL="install -p" EXTRA_CFLAGS="$MoreCFlags"

  popd

  # We install a collection of hooks for gdb that make it easier to debug
  # executables linked against libpython3* (such as /usr/bin/python3 itself)
  #
  # These hooks are implemented in Python itself (though they are for the version
  # of python that gdb is linked with, in this case Python 2.7)
  #
  # gdb-archer looks for them in the same path as the ELF file, with a -gdb.py suffix.
  # We put them in the debuginfo package by installing them to e.g.:
  #  /usr/lib/debug/usr/lib/libpython3.2.so.1.0.debug-gdb.py
  #
  # See https://fedoraproject.org/wiki/Features/EasierPythonDebugging for more
  # information
  #
  # Copy up the gdb hooks into place; the python file will be autoloaded by gdb
  # when visiting libpython.so, provided that the python file is installed to the
  # same path as the library (or its .debug file) plus a "-gdb.py" suffix, e.g:
  #  /usr/lib/debug/usr/lib64/libpython3.2.so.1.0.debug-gdb.py
  # (note that the debug path is /usr/lib/debug for both 32/64 bit)
  #
  # Initially I tried:
  #  /usr/lib/libpython3.1.so.1.0-gdb.py
  # but doing so generated noise when ldconfig was rerun (rhbz:562980)
  #
%if 0%{?with_gdb_hooks}
  DirHoldingGdbPy=%{_prefix}/lib/debug/%{_libdir}
  PathOfGdbPy=$DirHoldingGdbPy/$PyInstSoName.debug-gdb.py

  mkdir -p %{buildroot}$DirHoldingGdbPy
  cp Tools/gdb/libpython.py %{buildroot}$PathOfGdbPy
%endif # with_gdb_hooks

  echo FINISHED: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
}

# Use "InstallPython" to support building with different configurations:

# Install the "debug" build first, so that we can move some files aside
%if 0%{?with_debug_build}
InstallPython debug \
  %{py_INSTSONAME_debug} \
  -O0
%endif # with_debug_build

# Now the optimized build:
InstallPython optimized \
  %{py_INSTSONAME_optimized}

install -d -m 0755 ${RPM_BUILD_ROOT}%{pylibdir}/site-packages/__pycache__

mv ${RPM_BUILD_ROOT}%{_bindir}/2to3 ${RPM_BUILD_ROOT}%{_bindir}/python3-2to3

# Development tools
install -m755 -d ${RPM_BUILD_ROOT}%{pylibdir}/Tools
install Tools/README ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/freeze ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/i18n ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/pynche ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/scripts ${RPM_BUILD_ROOT}%{pylibdir}/Tools/

# Documentation tools
install -m755 -d %{buildroot}%{pylibdir}/Doc
cp -ar Doc/tools %{buildroot}%{pylibdir}/Doc/

# Demo scripts
cp -ar Tools/demo %{buildroot}%{pylibdir}/Tools/

# Fix for bug #136654
rm -f %{buildroot}%{pylibdir}/email/test/data/audiotest.au %{buildroot}%{pylibdir}/test/audiotest.au

%if "%{_lib}" == "lib64"
install -d -m 0755 %{buildroot}/%{_prefix}/lib/python%{pybasever}/site-packages/__pycache__
%endif

# Make python3-devel multilib-ready (bug #192747, #139911)
%global _pyconfig32_h pyconfig-32.h
%global _pyconfig64_h pyconfig-64.h

%ifarch %{power64} s390x x86_64 ia64 alpha sparc64 aarch64 %{mips64}
%global _pyconfig_h %{_pyconfig64_h}
%else
%global _pyconfig_h %{_pyconfig32_h}
%endif

# ABIFLAGS, LDVERSION and SOABI are in the upstream Makefile
%global ABIFLAGS_optimized m
%global ABIFLAGS_debug     dm

%global LDVERSION_optimized %{pybasever}%{ABIFLAGS_optimized}
%global LDVERSION_debug     %{pybasever}%{ABIFLAGS_debug}

%global SOABI_optimized cpython-%{pyshortver}%{ABIFLAGS_optimized}-%{_arch}-linux%{_gnu}
%global SOABI_debug     cpython-%{pyshortver}%{ABIFLAGS_debug}-%{_arch}-linux%{_gnu}

%if 0%{?with_debug_build}
%global PyIncludeDirs python%{LDVERSION_optimized} python%{LDVERSION_debug}

%else
%global PyIncludeDirs python%{LDVERSION_optimized}
%endif

for PyIncludeDir in %{PyIncludeDirs} ; do
  mv %{buildroot}%{_includedir}/$PyIncludeDir/pyconfig.h \
     %{buildroot}%{_includedir}/$PyIncludeDir/%{_pyconfig_h}
  cat > %{buildroot}%{_includedir}/$PyIncludeDir/pyconfig.h << EOF
#include <bits/wordsize.h>

#if __WORDSIZE == 32
#include "%{_pyconfig32_h}"
#elif __WORDSIZE == 64
#include "%{_pyconfig64_h}"
#else
#error "Unknown word size"
#endif
EOF
done

# Fix for bug 201434: make sure distutils looks at the right pyconfig.h file
# Similar for sysconfig: sysconfig.get_config_h_filename tries to locate
# pyconfig.h so it can be parsed, and needs to do this at runtime in site.py
# when python starts up (bug 653058)
#
# Split this out so it goes directly to the pyconfig-32.h/pyconfig-64.h
# variants:
sed -i -e "s/'pyconfig.h'/'%{_pyconfig_h}'/" \
  %{buildroot}%{pylibdir}/distutils/sysconfig.py \
  %{buildroot}%{pylibdir}/sysconfig.py

# Switch all shebangs to refer to the specific Python version.
LD_LIBRARY_PATH=./build/optimized ./build/optimized/python \
  Tools/scripts/pathfix.py \
  -i "%{_bindir}/python%{pybasever}" \
  %{buildroot}

# Remove shebang lines from .py files that aren't executable, and
# remove executability from .py files that don't have a shebang line:
find %{buildroot} -name \*.py \
  \( \( \! -perm /u+x,g+x,o+x -exec sed -e '/^#!/Q 0' -e 'Q 1' {} \; \
  -print -exec sed -i '1d' {} \; \) -o \( \
  -perm /u+x,g+x,o+x ! -exec grep -m 1 -q '^#!' {} \; \
  -exec chmod a-x {} \; \) \)

# .xpm and .xbm files should not be executable:
find %{buildroot} \
  \( -name \*.xbm -o -name \*.xpm -o -name \*.xpm.1 \) \
  -exec chmod a-x {} \;

# Remove executable flag from files that shouldn't have it:
chmod a-x \
  %{buildroot}%{pylibdir}/distutils/tests/Setup.sample \
  %{buildroot}%{pylibdir}/Tools/README

# Get rid of DOS batch files:
find %{buildroot} -name \*.bat -exec rm {} \;

# Get rid of backup files:
find %{buildroot}/ -name "*~" -exec rm -f {} \;
find . -name "*~" -exec rm -f {} \;
rm -f %{buildroot}%{pylibdir}/LICENSE.txt
# Junk, no point in putting in -test sub-pkg
rm -f ${RPM_BUILD_ROOT}/%{pylibdir}/idlelib/testcode.py*

# Get rid of stray patch file from buildroot:
rm -f %{buildroot}%{pylibdir}/test/test_imp.py.apply-our-changes-to-expected-shebang # from patch 4

# Fix end-of-line encodings:
find %{buildroot}/ -name \*.py -exec sed -i 's/\r//' {} \;

# Fix an encoding:
iconv -f iso8859-1 -t utf-8 %{buildroot}/%{pylibdir}/Demo/rpc/README > README.conv && mv -f README.conv %{buildroot}/%{pylibdir}/Demo/rpc/README

# Note that
#  %{pylibdir}/Demo/distutils/test2to3/setup.py
# is in iso-8859-1 encoding, and that this is deliberate; this is test data
# for the 2to3 tool, and one of the functions of the 2to3 tool is to fixup
# character encodings within python source code

# Do bytecompilation with the newly installed interpreter.
# This is similar to the script in macros.pybytecompile
# compile *.pyc
find %{buildroot} -type f -a -name "*.py" -print0 | \
    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} -O -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("%{buildroot}")[2], optimize=opt) for opt in range(3) for f in sys.argv[1:]]' || :

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find %{buildroot} \
    -perm 555 -exec chmod 755 {} \;

# Install macros for rpm:
mkdir -p %{buildroot}/%{_rpmconfigdir}/macros.d/
install -m 644 %{SOURCE3} %{buildroot}/%{_rpmconfigdir}/macros.d/

# Ensure that the curses module was linked against libncursesw.so, rather than
# libncurses.so (bug 539917)
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

#
# Systemtap hooks:
#
%if 0%{?with_systemtap}
# Install a tapset for this libpython into tapsetdir, fixing up the path to the
# library:
mkdir -p %{buildroot}%{tapsetdir}
%ifarch %{power64} s390x x86_64 ia64 alpha sparc64 aarch64 %{mips64}
%global libpython_stp_optimized libpython%{pybasever}-64.stp
%global libpython_stp_debug     libpython%{pybasever}-debug-64.stp
%else
%global libpython_stp_optimized libpython%{pybasever}-32.stp
%global libpython_stp_debug     libpython%{pybasever}-debug-32.stp
%endif

sed \
   -e "s|LIBRARY_PATH|%{_libdir}/%{py_INSTSONAME_optimized}|" \
   %{_sourcedir}/libpython.stp \
   > %{buildroot}%{tapsetdir}/%{libpython_stp_optimized}

%if 0%{?with_debug_build}
# In Python 3, python3 and python3-debug don't point to the same binary,
# so we have to replace "python3" with "python3-debug" to get systemtap
# working with debug build
sed \
   -e "s|LIBRARY_PATH|%{_libdir}/%{py_INSTSONAME_debug}|" \
   -e 's|"python3"|"python3-debug"|' \
   %{_sourcedir}/libpython.stp \
   > %{buildroot}%{tapsetdir}/%{libpython_stp_debug}
%endif # with_debug_build

%endif # with_systemtap

# Rename the script that differs on different arches to arch specific name
mv %{buildroot}%{_bindir}/python%{LDVERSION_optimized}-{,`uname -m`-}config
echo -e '#!/bin/sh\nexec `dirname $0`/python%{LDVERSION_optimized}-`uname -m`-config "$@"' > \
  %{buildroot}%{_bindir}/python%{LDVERSION_optimized}-config
echo '[ $? -eq 127 ] && echo "Could not find python%{LDVERSION_optimized}-`uname -m`-config. Look around to see available arches." >&2' >> \
  %{buildroot}%{_bindir}/python%{LDVERSION_optimized}-config
  chmod +x %{buildroot}%{_bindir}/python%{LDVERSION_optimized}-config

# Remove stuff that would conflict with python3 package
mv %{buildroot}%{_bindir}/python{3,%{pyshortver}}
rm %{buildroot}%{_bindir}/*3
rm %{buildroot}%{_bindir}/python3-*
rm %{buildroot}%{_bindir}/pyvenv
rm %{buildroot}%{_libdir}/libpython3.so
rm %{buildroot}%{_mandir}/man1/python3.1*
rm %{buildroot}%{_libdir}/pkgconfig/python3.pc

# ======================================================
# Running the upstream test suite
# ======================================================

%check

# first of all, check timestamps of bytecode files
find %{buildroot} -type f -a -name "*.py" -print0 | \
    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} %{SOURCE8}

# For ppc64 we need a larger stack than default (rhbz#1292462)
%ifarch %{power64}
  ulimit -a
  ulimit -s 16384
%endif

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
    --verbose --findleaks \
    -x test_distutils \
    %ifarch ppc64le aarch64
    -x test_faulthandler \
    %endif
    %ifarch %{mips64}
    -x test_ctypes \
    %endif
    %ifarch %{power64} s390 s390x armv7hl aarch64 %{mips}
    -x test_gdb
    %endif

  echo FINISHED: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

}

%if 0%{run_selftest_suite}

# Check each of the configurations:
%if 0%{?with_debug_build}
CheckPython debug
%endif # with_debug_build
CheckPython optimized

%endif # run_selftest_suite


# ======================================================
# Scriptlets
# ======================================================

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig


%files
%defattr(-, root, root)
%doc LICENSE README
%doc Misc/README.valgrind Misc/valgrind-python.supp Misc/gdbinit

%{_bindir}/pydoc%{pybasever}
%{_bindir}/python%{pybasever}
%{_bindir}/python%{pyshortver}
%{_bindir}/python%{pybasever}m
%{_bindir}/pyvenv-%{pybasever}
%{_mandir}/*/*

%{pylibdir}/

%if "%{_lib}" == "lib64"
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages/__pycache__/
%endif

%{_libdir}/%{py_INSTSONAME_optimized}
%if 0%{?with_systemtap}
%dir %(dirname %{tapsetdir})
%dir %{tapsetdir}
%{tapsetdir}/%{libpython_stp_optimized}
%doc systemtap-example.stp pyfuntop.stp
%endif

%{_includedir}/python%{LDVERSION_optimized}/

%{_bindir}/python%{pybasever}-config
%{_bindir}/python%{LDVERSION_optimized}-config
%{_bindir}/python%{LDVERSION_optimized}-*-config
%{_libdir}/libpython%{LDVERSION_optimized}.so
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}.pc
%{_libdir}/pkgconfig/python-%{pybasever}.pc
%exclude %{_rpmconfigdir}/macros.d/macros.pybytecompile%{pybasever}

%{_bindir}/2to3-%{pybasever}
%{_bindir}/idle%{pybasever}

# https://bugzilla.redhat.com/show_bug.cgi?id=1476593
%exclude /usr/lib/debug%{_libdir}/__pycache__/libpython%{pybasever}m.so.1.0.debug-gdb.cpython-%{pyshortver}.*py*
%exclude /usr/lib/debug%{_libdir}/libpython%{pybasever}m.so.1.0.debug-gdb.py

%if 0%{?with_debug_build}
%{_bindir}/python%{LDVERSION_debug}

%{_libdir}/%{py_INSTSONAME_debug}
%if 0%{?with_systemtap}
%{tapsetdir}/%{libpython_stp_debug}
%endif

%{_includedir}/python%{LDVERSION_debug}
%{_bindir}/python%{LDVERSION_debug}-config
%{_libdir}/libpython%{LDVERSION_debug}.so
%{_libdir}/libpython%{LDVERSION_debug}.so.1.0
%{_libdir}/pkgconfig/python-%{LDVERSION_debug}.pc

%endif # with_debug_build


# ======================================================
# Finally, the changelog:
# ======================================================

%changelog
* Tue Dec 05 2017 Miro Hrončok <mhroncok@redhat.com> - 3.5.4-2
- Fix for CVE-2017-1000158
- rhbz#1519603: https://bugzilla.redhat.com/show_bug.cgi?id=1519603

* Mon Oct 30 2017 Charalampos Stratakis <cstratak@redhat.com> - 3.5.4-1
- Rebased to version 3.5.4

* Mon Aug 14 2017 David "Sanqui" Labský <dlabsky@redhat.com> - 3.5.3-5
- Drop unused db4-devel dependency

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 26 2017 Charalampos Stratakis <cstratak@redhat.com> - 3.5.3-2
- Fix test_alpn_protocols from test_ssl

* Thu May 11 2017 Charalampos Stratakis <cstratak@redhat.com> - 3.5.3-1
- Rebased to version 3.5.3 from F25
- Enable profile guided optimizations for x86_64 and i686 architectures
- Make pip installable in a new venv when using the --system-site-packages flag
- Fix syntax error in %%py_byte_compile macro
- Add patch 259 to work around magic number bump in Python 3.5.3

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.2-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jan 12 2017 Igor Gnatenko <ignatenko@redhat.com> - 3.5.2-8
- Rebuild for readline 7.x

* Tue Jan 10 2017 Charalampos Stratakis <cstratak@redhat.com> - 3.5.2-7
- Require glibc >= 2.24.90-26 (rhbz#1410644)

* Thu Jan 05 2017 Miro Hrončok <mhroncok@redhat.com> - 3.5.2-6
- Don't blow up on EL7 kernel (random generator) (rhbz#1410175, rhbz#1410187)

* Sun Jan 01 2017 Miro Hrončok <mhroncok@redhat.com> - 3.5.2-5
- Update description

* Sun Jan 01 2017 Miro Hrončok <mhroncok@redhat.com> - 3.5.2-4
- Add patch for OpenSSL 1.1.0

* Fri Oct 21 2016 Miro Hrončok <mhroncok@redhat.com> - 3.5.2-3
- Reword the description

* Tue Sep 13 2016 Miro Hrončok <mhroncok@redhat.com> - 3.5.2-2
- Fixed .pyc bytecompilation
- Remove unused configure flags

* Mon Aug 15 2016 Tomas Orsava <torsava@redhat.com> - 3.5.2-1
- Rebased to version 3.5.2 from F26

* Tue Aug 09 2016 Miro Hrončok <mhroncok@redhat.com> - 3.5.1-14
- Imported from F25
