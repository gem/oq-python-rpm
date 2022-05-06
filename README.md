# oq-python-rpm
Custom Python RPM packages for OpenQuake, supporting RHEL/CentOS 7, RHEL/CentOS 8 and Fedora.

The corresponding Ubuntu packages can be found at https://github.com/gem/oq-python-deb/.

## Build

```bash
$ dnf download --source python38
$ rpm -ivh python3-3.8.2-2.fc32.src.rpm
$ spectool -g -R ~/rpmbuild/SPECS/oq-python38.spec
$ rpmbuild -bs ~/rpmbuild/SPECS/oq-python38.spec
$ mock -r epel-8-x86_64 ~/rpmbuild/SRPMS/oq-python38-3.8.2-1.fc32.src.rpm
```

## Python 3.6

Based on https://src.fedoraproject.org/rpms/python36/c/0b48557f62994885b6b2119afa98ab215e573b7c?branch=master

Provides Python 3.6 in `/opt/openquake`

## Python 3.7

Based on https://src.fedoraproject.org/rpms/python37/c/f54cef86717adf4f5374820c3d5314f75b340b8b?branch=master

Provides Python 3.7 in `/opt/openquake`

## Python 3.8

Based on https://src.fedoraproject.org/rpms/python38/c/32fce1d319fd583639b44057ceab2c6046f19eaf?branch=f31

Provides Python 3.8 in `/opt/openquake`

## Python 3.9

Based on https://src.fedoraproject.org/rpms/python3.9/c/fefc6815e502651c34d71ba02b0b67fade07e601?branch=rawhide

Provides Python 3.9 in `/opt/openquake`
