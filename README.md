# oq-python-dist
Custom Python RPM packages for OpenQuake, supporting RHEL/CentOS 7 and Fedora. The corresponding Ubuntu package can be found at https://github.com/gem/oq-python-deb/.

## Build

```bash
$ spectool -g -R oq-python36.spec
$ rpmbuild -bs oq-python36.spec
$ mock -r epel-7-x86_64 oq-python36-3.6.6-1.fc28.src.rpm
```

Based on https://src.fedoraproject.org/cgit/rpms/python36.git/tree/?id=1d12e5b385977ba392f81d8d665e3b2e21cea53a

Provides Python 3.6 in `/opt/openquake`
