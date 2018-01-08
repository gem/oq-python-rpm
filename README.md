# oq-python-dist
Python Linux packages for OpenQuake, currently supporting RHEL/CentOS 7

## Build RPM

```bash
$ spectool -g -R oq-python35.spec
$ rpmbuild -bs oq-python35.spec
$ mock -r mock -r epel-7-x86_64
$ oq-python35-3.5.4-1.fc27.src.rpm
```
