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
%global general_version %{pybasever}.16
%global upstream_version %{general_version}%{?prerel}
Version: %{general_version}%{?prerel:~%{prerel}}
Release: 1%{?dist}
License: Python

# ==================================
# Conditionals controlling the build
# ==================================

# Note that the bcond macros are named for the CLI option they create.
# "%%bcond_without" means "ENABLE by default and create a --without option"


# =====================
# General global macros
# =====================

%global pylibdir %{_libdir}/python%{pybasever}
%global dynload_dir %{pylibdir}/lib-dynload

# ABIFLAGS, LDVERSION and SOABI are in the upstream configure.ac
# See PEP 3149 for some background: http://www.python.org/dev/peps/pep-3149/
%global ABIFLAGS_optimized %{nil}
%global LDVERSION_optimized %{pybasever}%{ABIFLAGS_optimized}
%global SOABI_optimized cpython-%{pyshortver}%{ABIFLAGS_optimized}-%{_arch}-linux%{_gnu}


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
%define __python3 %{_prefix}/%{_bindir}/python%{pybasever}
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
BuildRequires: desktop-file-utils
BuildRequires: expat-devel
BuildRequires: findutils
BuildRequires: gcc-c++
BuildRequires: gdbm-devel
BuildRequires: git-core
BuildRequires: glibc-devel
#BuildRequires: glibc-all-langpacks
BuildRequires: gmp-devel
BuildRequires: gnupg2
BuildRequires: libappstream-glib
BuildRequires: libffi-devel
BuildRequires: libtirpc-devel
BuildRequires: libGL-devel
BuildRequires: libuuid-devel
BuildRequires: make
BuildRequires: ncurses-devel

BuildRequires: openssl-devel
BuildRequires: pkgconfig
BuildRequires: readline-devel
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

%if 0%{?el7}
%else
BuildRequires: redhat-rpm-config >= 127
BuildRequires: libnsl2-devel
%endif

# workaround http://bugs.python.org/issue19804 (test_uuid requires ifconfig)
#BuildRequires: /usr/sbin/ifconfig


# =======================
# Source code and patches
# =======================

Source0: %{url}ftp/python/%{general_version}/Python-%{upstream_version}.tar.xz
Source1: %{url}ftp/python/%{general_version}/Python-%{upstream_version}.tar.xz.asc


# ==========================================
# Descriptions, and metadata for subpackages
# ==========================================

# We'll not provide this, on purpose
# No package in Fedora shall ever depend on flatpackage via this
%global __requires_exclude ^python\\(abi\\) = 3\\..$
%global __provides_exclude ^python\\(abi\\) = 3\\..$

Provides: oq-python3
Obsoletes: oq-python35 oq-python36 oq-python37 oq-python38

%description
Python %{pybasever} package for OpenQuake

# ======================================================
# The prep phase of the build:
# ======================================================

%prep
%setup -q -n Python-%{version}%{?prerel}

# Remove bundled libraries to ensure that we're using the system copy.
rm -r Modules/expat

#
#

# Remove files that should be generated by the build
# (This is after patching, so that we can use patches directly from upstream)
#rm configure pyconfig.h.in


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

echo gcc version
gcc --version

# Compile toolchain in EL7 is too old to support optimizations
# instead of using a custom newer gcc we disable optimizations on EL7
#%if %{with optimizations} && 0%{?el} >=8
#%global optimizations_flag "--enable-optimizations"
#%else
#%global optimizations_flag ""
#gcc --version
#%endif

# libmpdec (mpdecimal package in Fedora) is tightly coupled with the
# decimal module. We keep it bundled as to avoid incompatibilities
# with the packaged version.
# The version information can be found at Modules/_decimal/libmpdec/mpdecimal.h
# defined as MPD_VERSION.

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

  #Since we changed directories, we need to tell %%configure where to look.
  %global _configure $topdir/configure

  %configure \
    --with-platlibdir=%{_lib} \
    --with-system-expat \
    --with-system-ffi \
    --enable-loadable-sqlite-extensions \
    --with-dtrace \
    --with-ssl-default-suites=openssl \
    --with-lto \
    --enable-optimizations \
    --with-ensurepip

  %make_build EXTRA_CFLAGS="$CFLAGS $MoreCFlags"

  popd
  echo FINISHED: BUILD OF PYTHON FOR CONFIGURATION: $ConfName
}

BuildPython optimized

# ======================================================
# Installing the built code:
# ======================================================

%install

# As in %%build, remember the current directory
topdir=$(pwd)

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

    #INSTALL="install -p" \

  make \
    DESTDIR=%{buildroot} \
    EXTRA_CFLAGS="$MoreCFlags" \
    install

  popd

  echo FINISHED: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
}

InstallPython optimized

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

# Switch all shebangs to refer to the specific Python version.
# This currently only covers files matching ^[a-zA-Z0-9_]+\.py$,
# so handle files named using other naming scheme separately.
LD_LIBRARY_PATH=./build/optimized ./build/optimized/python \
  Tools/scripts/pathfix.py \
  -i "%{_bindir}/python%{pybasever}" -pn \
  %{buildroot}
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
#find %{buildroot} -type f -a -name "*.py" -print0 | \
#    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
#    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
#    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} -O -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("%{buildroot}")[2], optimize=opt) for opt in range(3) for f in sys.argv[1:]]' || :

# Since we have pathfix.py in bindir, this is created, but we don't want it
rm -rf %{buildroot}%{_bindir}/__pycache__

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find %{buildroot} -perm 555 -exec chmod 755 {} \;

# Provide python as python3
cp %{buildroot}%{_bindir}/python%{pybasever} %{buildroot}%{_bindir}/python

# ======================================================
# Running the upstream test suite
# ======================================================

%check

topdir=$(pwd)
CheckPython() {
  ConfName=$1
  ConfDir=$(pwd)/build/$ConfName

  echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

  # Note that we're running the tests using the version of the code in the
  # builddir, not in the buildroot.

  # Show some info, helpful for debugging test failures
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.pythoninfo

  # Run the upstream test suite, setting "WITHIN_PYTHON_RPM_BUILD" so that the
  # our non-standard decorators take effect on the relevant tests:
  #   @unittest._skipInRpmBuild(reason)
  #   @unittest._expectedFailureInRpmBuild
  # test_faulthandler.test_register_chain currently fails on ppc64le and
  #   aarch64, see upstream bug http://bugs.python.org/issue21131
  #WITHIN_PYTHON_RPM_BUILD= \
  #LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.regrtest \
  #  -wW --slowest --findleaks \
  #  -x test_distutils \
  #  -x test_bdist_rpm

  #WITHIN_PYTHON_RPM_BUILD= \
  #LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test

  echo FINISHED: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

}

CheckPython optimized

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
#
%{_bindir}/python3
%{_bindir}/python%{pybasever}
%{_bindir}/python
%{_bindir}/pydoc3
%{_bindir}/pydoc%{pybasever}
%{_bindir}/pip%{pybasever}
%{_bindir}/pip3
%{_bindir}/python3-config
%{_bindir}/python%{pybasever}-config
%{_mandir}
#
%{pylibdir}/
#
%if "%{_lib}" == "lib64"
%{_prefix}/lib/python%{pybasever}
%endif
#
%{_includedir}/python%{LDVERSION_optimized}/
#
%{_libdir}/libpython%{LDVERSION_optimized}.a
%dir %{_libdir}/pkgconfig
%{_libdir}/pkgconfig/python3.pc
%{_libdir}/pkgconfig/python3-embed.pc
%{_libdir}/pkgconfig/python-%{pybasever}.pc
%{_libdir}/pkgconfig/python-%{pybasever}-embed.pc
#
%{_bindir}/2to3
%{_bindir}/2to3-%{pybasever}
%{_bindir}/idle3
%{_bindir}/idle%{pybasever}
#
## Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=1476593
%undefine _debuginfo_subpackages
#
# ======================================================
# Finally, the changelog:
# ======================================================

%changelog
* Mon May 15 2023 Antonio Ettorre <antonio@openquake.org> - 3.9.16-1
- Upgrade to 3.9.16-1

* Mon May 9 2022 Antonio Ettorre <antonio@openquake.org> - 3.9.12-1
- First build of oq-python39 

