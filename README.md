# oq-python-dist
Custom Python RPM packages for OpenQuake, supporting RHEL/CentOS 7 and Fedora. The corresponding Ubuntu package can be found at https://github.com/gem/oq-python-deb/.

## Build

```bash
$ spectool -g -R oq-python35.spec
$ rpmbuild -bs oq-python35.spec
$ mock -r epel-7-x86_64 oq-python35-3.5.4-1.fc27.src.rpm
```

Based on https://src.fedoraproject.org/rpms/python35

Provides Python 3.5 in `/opt/openquake`
