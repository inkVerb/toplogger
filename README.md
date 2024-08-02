# toplogger
## `top` logger per-minute
*Service that keeps `top` logs every minute, per month, in `/var/log/toplogger/`*

## Create the simple Linux install package for `toplogger`
This is a guide to create an installer package for the `toplogger` service on:
1. Arch (Manjaro, Black Arch, et al)
2. Debian (Ubuntu, Kali, Mint, et al)
3. RPM (OpenSUSE, RedHat/CentOS, Fedora, et al)

Working examples for each already resides in this repository

### Create and install the `toplogger` package directly from this repo

| **Arch** :$ (& Manjaro, Black Arch)

```console
git clone https://github.com/inkVerb/toplogger.git
cd toplogger/arch
makepkg -si
```

| **Debian** :$ (& Ubuntu, Kali, Mint)

```console
git clone https://github.com/inkVerb/toplogger.git
cd toplogger/deb
dpkg-deb --build toplogger
sudo dpkg -i toplogger.deb
```

| **RedHat/CentOS** :$ (& Fedora)

```console
git clone https://github.com/inkVerb/toplogger.git
sudo dnf update
sudo dnf install rpm-build rpmdevtools
cp -rf toplogger/rpm/rpmbuild ~/
rpmbuild -ba ~/rpmbuild/SPECS/toplogger.spec
ls ~/rpmbuild/RPMS/noarch/
sudo rpm -i ~/rpmbuild/RPMS/noarch/toplogger-1.0.0-1.noarch.rpm  # Change filename if needed
rm -rf ~/rpmbuild
```

| **OpenSUSE** :$ (& Tumbleweed)

```console
git clone https://github.com/inkVerb/toplogger.git
cd toplogger/rpm
sudo zypper update
sudo zypper install rpm-build rpmdevtools
cp -r rpmbuild ~/
rpmbuild -ba ~/rpmbuild/SPECS/toplogger.spec
ls ~/rpmbuild/RPMS/noarch/
sudo rpm -i ~/rpmbuild/RPMS/noarch/toplogger-1.0.0-1.noarch.rpm  # Change filename if needed
rm -rf ~/rpmbuild
```

## Service Breakdown
- This explains the two simple files that make this service work
- The two files, plus one optional config, are the same for every architecture's installer package
  - The `.service` file goes in `/usr/systemd/system/`, not `/etc/systemd/system/` [because this is part of a package](https://bbs.archlinux.org/viewtopic.php?id=171461)
  - The `.sh` script is not intended to be executed from the command line, so it goes somewhere in `/lib/`
    - `/lib/` is a symlink to `/usr/lib/` across most architectures, so we use `/usr/lib/` directly
  - The config at `/etc/toplogger/conf`, if broken, has default contingencies in the `.sh` script
    - This will be removed on a purge, but not a simple remove
- The dependency is `systemd` since we are using systemd structure, not SysVinit or Upstart

| **`toplogger.sh`** : (`/usr/lib/toplogger/toplogger.sh` - `755`)

```bash
#!/bin/bash

# Get conf setting if there
if [ -f "/etc/toplogger/conf" ]; then
  interval=$(grep interval_seconds /etc/toplogger/conf | awk '{print $2}')

  # Wrong conf setting defaults to 60
  if [ $interval -gt 3600 ] || [ $interval -lt 30 ]; then
    interval=60    
  fi
else

  # No conf defaults to 60
  interval=60
fi

# The interval setting is done before the loop starts, so the script will need to be re-started before an config changes take effect; this means using `systemctl restart toplogger`

# Start an infinite loop with `while :`
while :; do
  # Always ensure the directory exists
  /usr/bin/mkdir -p /var/log/toplogger
  if [ -d "/var/log/toplogger" ]; then
    # Set some important dates with command substitutes inside command substitutes
    this_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) 0 month" +%B`
    last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -1 month" +%B`
    last_last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -2 month" +%B`
    time_stamp="$(/usr/bin/date +%Y-%m-%d_%H:%M:%S)"
    /usr/bin/mkdir -p /var/log/toplogger/${this_month}
    # Remove logs older than one month
    if [ ! -d "/var/log/toplogger/${this_month}" ] && [ -d "/var/log/toplogger/${last_month}" ]; then
      /usr/bin/rm -rf /var/log/toplogger/${last_last_month}
    fi
    # Make the log from one, single `top` iteration
    if [ -d "/var/log/toplogger" ]; then
      top -b -n 1 > /var/log/toplogger/${this_month}/${time_stamp}
    fi
  fi
  # Wait 60 seconds before looping again
  sleep $interval
done
```

| **`toplogger.service`** : (`/usr/lib/systemd/system/toplogger.service` - `644`)

```bash
[Unit]
Description=top logger per-minute

[Service]
ExecStart=/usr/lib/toplogger/toplogger.sh  # The script

[Install]
WantedBy=network.target  # Start looping as soon as the network starts, don't wait for multi-user
```

- This third file is used as a config in `/etc/`
  - If it does not exist, the script will default to `60`

| **`conf`** : (`/etc/toplogger/conf`)

```
interval_seconds 60  # Must be an integer within 30 to 3600
```

## Detailed instructions per architecture
Instructions explain each in detail to create these packages from scratch...

### I. Arch Linux Package (`toplogger-1.0.0-1-any.pkg.tar.zst`)
*Arch package directory structure:*

| **`arch/`** :

```
arch/
├─ PKGBUILD
├─ conf
├─ toplogger.service
└─ toplogger.sh
```

- Create directory: `arch`
- In `arch/` create file: `PKGBUILD`

| **`arch/PKGBUILD`** :

```
pkgname=toplogger
pkgver=1.0.0
pkgrel=1
pkgdesc="top logs per-minute"
url="https://github.com/inkVerb/toplogger"
arch=('any')
license=('GPL')
depends=('systemd')
source=("$pkgname.sh" "$pkgname.service")
sha256sums=('SKIP' 'SKIP')

package() {
  install -Dm755 "$srcdir/$pkgname.sh" "$pkgdir/usr/lib/$pkgname/$pkgname.sh"
  install -Dm644 "$srcdir/$pkgname.service" "$pkgdir/usr/lib/systemd/system/$pkgname.service"
}

post_install() {
  systemctl enable $pkgname.service
  systemctl start $pkgname.service
}
```

- Place files `conf`, `toplogger.sh` & `toplogger.service` in the same directory as `PKGBUILD`
- Build package:
  - Navigate to directory `arch/`
  - Run this, then the package will be built, then installed with `pacman`:

| **Build & install Arch package** :$ (in one command)

```console
makepkg -i
```

- Use this to build and install in two steps:

| **Build, *then* install Arch package** :$ (first line produces the `.pkg.tar.zst` file for repos or manual install)

```console
makepkg
sudo pacman -U toplogger-1.0.0-1-any.pkg.tar.zst
```

- Special notes about Arch:
  - We don't need to use the `-s` flag with `makepkg` this time because of the singular dependency issue
    - The `.service` structure needs `systemd`
    - If `systemd` was not already in use, then it could be SysVinit or Upstart, which `systemd` should conflict with
  - The name of the directory containing the package files does not matter
  - `PKGBUILD` is the instruction file, not a directory as might be expected with other package builders
  - `makepkg` must be run from the same directory containing `PKGBUILD`
  - The `.pkg.tar.zst` file will appear inside the containing directory

| **Uninstall Arch package** :$ (optional)

```console
sudo pacman -R toplogger
```

### II. Debian Package (`toplogger.deb`)
*Debian package directory structure:*

| **`deb/`** :

```
deb/
└─ toplogger/
   ├─ DEBIAN/
   │  ├─ control
   │  ├─ postinst
   │  ├─ postrm
   │  └─ prerm
   └─ usr/
   │ └─ lib/
   │     ├─ systemd/
   │     │  └─ system/
   │     │     └─ toplogger.service
   │     └─ toplogger/
   │        └─ toplogger.sh
   └─ etc/
      └─ toplogger/
         └─ conf
```

- Create directories: `deb/toplogger/DEBIAN`
- In `DEBIAN/` create file: `control`

| **`deb/toplogger/DEBIAN/control`** :

```
Package: toplogger
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Maintainer: inkVerb <toplogger@inkisaverb.com>
Depends: systemd
Description: top logs per-minute
```

- In `DEBIAN/` create file: `postinst`
  - Make it executable with :$ `chmod +x DEBIAN/postinst`

| **`deb/toplogger/DEBIAN/postinst`** :

```
#!/bin/bash

# exit from any errors
set -e

# git clone and move proper folder into place
install -Dm755 /usr/lib/toplogger/toplogger.sh /usr/lib/toplogger/toplogger.sh
install -Dm644 /usr/lib/systemd/system/toplogger.service /usr/lib/systemd/system/toplogger.service
install -Dm644 /etc/toplogger/conf /etc/toplogger/conf

# Service
systemctl enable toplogger.service
systemctl start toplogger.service
```

- In `DEBIAN/` create file: `prerm`
  - Make it executable with :$ `chmod +x DEBIAN/prerm`

| **`deb/toplogger/DEBIAN/prerm`** : (disable services after remove)

```
#!/bin/bash

# exit from any errors
set -e

systemctl stop toplogger
systemctl disable toplogger

```

- In `DEBIAN/` create file: `postrm`
  - Make it executable with :$ `chmod +x DEBIAN/postrm`

| **`deb/toplogger/DEBIAN/postrm`** : (remove `/etc/` configs only on purge)

```
#!/bin/bash

# exit from any errors
set -e

if [ "$1" = "purge" ]; then
    rm -rf /etc/toplogger
fi
```

- Create directories:
  - `deb/toplogger/etc/toplogger/`
  - `deb/toplogger/usr/lib/toplogger/`
  - `deb/toplogger/usr/lib/systemd/system/`
- Place file `conf` in `deb/toplogger/etc/toplogger/`
- Place file `toplogger.sh` in `deb/toplogger/usr/lib/toplogger/`
- Place file `toplogger.service` in `deb/toplogger/usr/lib/systemd/system/`
- Build package:
  - Navigate to directory `deb/`
  - Run this, then the package will be built, then installed:

| **Build, *then* install Debian package** :$

```console
dpkg-deb --build toplogger  # Create the .deb package
sudo dpkg -i toplogger.deb  # Install the package
```

- Special notes about Debian
  - The script file at `usr/lib/toplogger/toplogger.sh` does not need to be executable
    - This is because this installer uses a `postinst` script
    - This script will set the permissions in the command `install -Dm755`
  - The directory of the package files (`toplogger/`) will be the same as the package installer's `.deb` basename
  - The package installer will appear at `toplogger.deb` in the same directory as (`toplogger/`) regardless of the PWD from where the `dpkg-deb --build` command was run
    - For `deb/toplogger` it will be at `deb/toplogger.deb`

| **Uninstall Debian package** :$ (optional)

```console
sudo apt-get remove toplogger
```

### III. RPM Package (`toplogger-1.0.0-1.noarch.rpm`)
*RPM package directory structure:*

***Note this is probably broken on RedHat distros because of the lacking `pandoc` package***

| **`rpm/`** :

```
rpm/
└─ rpmbuild/
   ├─ SPECS/
   │  └─ toplogger.spec
   └─ SOURCES/
      ├─ conf
      ├─ toplogger.service
      └─ toplogger.sh
```

- Create directories: `rpm/rpmbuild/SPECS`
- In `SPECS/` create file: `toplogger.spec`

| **`rpm/rpmbuild/SPECS/toplogger.spec`** :

```
Name:           toplogger
Version:        1.0.0
Release:        1%{?dist}
Summary:        top logs per-minute

License:        GPL
URL:            https://github.com/inkVerb/toplogger

BuildArch:      noarch
Requires:       systemd

%description
Service that keeps top logs every minute, per month, in /var/log/toplogger/

%prep
echo "####################################################
We are creating the talking penguin RPM installer...
Other commands could go here...
####################################################"

%build
# We could put some commands here if we needed to build from source

%install
install -Dm755 "$RPM_SOURCE_DIR/toplogger.sh" "$RPM_BUILD_ROOT/usr/lib/toplogger/toplogger.sh"
install -Dm644 "$RPM_SOURCE_DIR/toplogger.service" "$RPM_BUILD_ROOT/usr/lib/systemd/system/toplogger.service"
install -Dm644 "$RPM_SOURCE_DIR/conf" "$RPM_BUILD_ROOT/etc/toplogger/conf"

%post
systemctl daemon-reload
systemctl enable toplogger
systemctl start toplogger

%preun
if [ $1 -eq 0 ]; then
  systemctl stop toplogger
  systemctl disable toplogger
  systemctl daemon-reload
fi

%postun
if [ $1 -eq 0 ]; then
  rm -rf /etc/toplogger
fi

%files
/usr/lib/toplogger/toplogger.sh
/usr/lib/systemd/system/toplogger.service
/etc/toplogger/conf

%config(noreplace)
/etc/toplogger/conf

%changelog
* Thu Jan 01 1970 Jesse <toplogger@inkisaverb.com> - 1.0.0-1
- Something started
```

- Create directory: `rpm/rpmbuild/SOURCES/`
- Place files `conf`, `toplogger.sh` & `toplogger.service` in directory `rpm/rpmbuild/SOURCES/`
- Install the `rpm-build` and `rpmdevtools` packages

| **RedHat/CentOS** :$

```console
sudo dnf update
sudo dnf install rpm-build rpmdevtools
```

| **OpenSUSE** :$

```console
sudo zypper update
sudo zypper install rpm-build rpmdevtools
```

- Build package:
  - Navigate to directory `rpm/`
  - Run the following commands:

| **Build, *then* install RPM package** :$

```console
cp -r rpmbuild ~/
rpmbuild -ba ~/rpmbuild/SPECS/toplogger.spec                     # Create the .rpm package
ls ~/rpmbuild/RPMS/noarch/                                       # Check the .rpm filename
sudo rpm -i ~/rpmbuild/RPMS/noarch/toplogger-1.0.0-1.noarch.rpm  # Install the package (filename may be different)
```

- Special notes about RPM:
  - RPM requires the build be done from `~/rpmbuild/`
  - The resulting `.rpm` fill will be at: `~/rpmbuild/RPMS/noarch/toplogger-1.0.0-1.noarch.rpm`
    - This file might actually have a different name, but should be in the same directory (`~/rpmbuild/RPMS/noarch/`)
  - `noarch` means it works on any architecture
    - This part of the filename was set in the `.spec` file with `BuildArch: noarch`

| **Uninstall RedHat/CentOS package** :$ (optional)

```console
sudo dnf remove toplogger
```

| **Uninstall OpenSUSE package** :$ (optional)

```console
sudo zypper remove toplogger
```