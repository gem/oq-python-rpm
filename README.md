# oq-python-dist
Python Linux packages for OpenQuake, currently supporting RHEL/CentOS 7

## RedHat

```bash
$ spectool -g -R oq-python35.spec
$ rpmbuild -bs oq-python35.spec
# Tests fails when using systemd-nspawn chroots, so passing --old-chroot
$ mock -r epel-7-x86_64 --old-chroot oq-python35-3.5.4-1.fc27.src.rpm
```

Based on http://pkgs.fedoraproject.org/cgit/rpms/python35.git/
Provides Python 3.5 in `/opt/openquake`
