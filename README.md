# toplogger
## `top` logger per-minute
*Service that keeps `top` logs every minute, per month, in `/var/log/toplogger/`, protected by AppArmor*

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

sudo systemctl enable toplogger
sudo systemctl start toplogger
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
- The two files, plus two optional configs and the AppArmor profile, are the same for every architecture's installer package
  - The `.service` file goes in `/usr/systemd/system/`, not `/etc/systemd/system/` [because this is part of a package](https://bbs.archlinux.org/viewtopic.php?id=171461)
  - The `.sh` script is not intended to be executed from the command line, so it goes somewhere in `/usr/lib/`
    - `/lib/` is a symlink to `/usr/lib/` across most architectures, so we use `/usr/lib/` directly
  - The configs at `/etc/toplogger/conf` & `/etc/toplogger/logdir`, if broken, have default contingencies in the `.sh` script
    - *If changed*, they will be removed on a purge, but not a simple remove
    - If they are not changed, then the package manager will recognize them from the files that shipped and remove them when the package is removed
  - AppArmor profiles are stored in `/etc/apparmor.d/`
    - The profile files are usually named after the primary executable file's location they govern
      - `usr.lib.toplogger.toplogger.sh` (for `/usr/lib/toplogger/toplogger.sh`)
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

# Get directory setting if there
if [ -f "/etc/toplogger/logdir" ]; then
  logdir=$(cat /etc/toplogger/logdir | awk '{print $1}')
else

  # No conf defaults to /var/log/toplogger
  logdir="/var/log/toplogger"
fi

# The interval setting is done before the loop starts, so the script will need to be re-started before an config changes take effect; this means using `systemctl restart toplogger`

# Start an infinite loop with `while :`
while :; do
  # Always ensure the directory exists
  /usr/bin/mkdir -p $logdir
  if [ -d "$logdir" ]; then
    # Set some important dates with command substitutes inside command substitutes
    this_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) 0 month" +%B`
    last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -1 month" +%B`
    last_last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -2 month" +%B`
    time_stamp="$(/usr/bin/date +%Y-%m-%d_%H:%M:%S)"
    /usr/bin/mkdir -p $logdir/${this_month}
    # Remove logs older than one month
    if [ ! -d "$logdir/${this_month}" ] && [ -d "$logdir/${last_month}" ]; then
      /usr/bin/rm -rf $logdir/${last_last_month}
    fi
    # Make the log from one, single `top` iteration
    if [ -d "$logdir" ]; then
      top -b -n 1 > $logdir/${this_month}/${time_stamp}
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
  - It is included in the package and copied into place

| **`conf`** : (`/etc/toplogger/conf`)

```
# This is a config file for toplogger
interval_seconds 60  # Must be an integer within 30 to 3600
```

- This fourth file is used as a config in `/etc/`
  - If it does not exist, the script will default to `/var/log/toplogger`
  - It is not included in the package, but is created using `echo`

| **`logdir`** : (`/etc/toplogger/logdir`)

```
/var/log/toplogger  # Directory where logs are sorted and kept
```

| **`usr.lib.toplogger.toplogger.sh`** : (AppArmor profile at `/etc/apparmor.d/usr.lib.toplogger.toplogger.sh`)

```
#include <tunables/global>

/usr/lib/toplogger/toplogger.sh {
    # Include necessary abstractions
    #include <abstractions/base>
    
    # Allow read access to configuration files
    /etc/toplogger/** r,

    # Allow read & write access to log files
    /var/log/toplogger/** rw,
    
    # Allow execution of the script
    /usr/lib/toplogger/toplogger.sh ix,
    
    # Allow read access to the service file
    /usr/lib/systemd/system/toplogger.service r,
    
    # Deny everything else by default
    deny /etc/** w,
    deny /usr/** w,
    deny /var/** w,
}
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
├─ toplogger.sh
└─ usr.lib.toplogger.toplogger.sh
```

- Create directory: `arch`
- In `arch/` create file: `PKGBUILD`

| **`arch/PKGBUILD`** :

```
# Maintainer: Ink Is A Verb <codes@inkisaverb.com>
pkgname=toplogger
pkgver=1.0.0
pkgrel=1
pkgdesc="top logs per-minute"
url="https://github.com/inkVerb/toplogger"
arch=('any')
license=('GPL')
depends=('systemd')
source=("$pkgname.sh" "$pkgname.service" "conf")
sha256sums=('SKIP' 'SKIP' 'SKIP')
# Preserve when uninstalled, delete when purged
backup=("etc/$pkgname/conf" "etc/$pkgname/logdir")

package() {

  install -Dm755 "$srcdir/$pkgname.sh" "$pkgdir/usr/lib/$pkgname/$pkgname.sh"
  install -Dm644 "$srcdir/$pkgname.service" "$pkgdir/usr/lib/systemd/system/$pkgname.service"
  install -Dm644 "$srcdir/conf" "$pkgdir/etc/$pkgname/conf"
  install -Dm644 "$srcdir/usr.lib.$pkgname.$pkgname.sh" "$pkgdir/etc/apparmor.d/usr.lib.$pkgname.$pkgname.sh"

  echo "/var/log/$pkgname  # Directory where logs are sorted and kept" > "$pkgdir/etc/$pkgname/logdir"
  
}

```

- Place files `conf`, `toplogger.sh`, `toplogger.service` & `usr.lib.toplogger.toplogger.sh` in the same directory as `PKGBUILD`
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
  - `systemctl` cannot enable, start, stop, or disable the service from the package installation
    - This is an [old problem part of an old discussion](https://superuser.com/questions/688733/)
    - This is because of the way that `pacman` uses `chroot` to install the package
    - The service will need to be enabled, started, stopped, disabled and removed manually *after* the installation or removal
      - `systemctl enable toplogger`, `systemctl start toplogger`, `systemctl stop toplogger`, `systemctl disable toplogger`
    - The same goes for AppArmor without rebooting
      - This assumes that AppArmor is even working, which it is not by default on Arch
      - `apparmor_parser -r /etc/apparmor.d/usr.lib.toplogger.toplogger.sh`, `aa-enforce /etc/apparmor.d/usr.lib.toplogger.toplogger.sh`, `aa-disable /etc/apparmor.d/usr.lib.toplogger.toplogger.sh`
    - This relates to the nature for Arch Linux to be minimalist, part of its appeal to some developers
      - There may be a work-around that includes a "post install" script and "install hook", but it must also disable the service on package removal, making it very complex to have the package manager handle `systemctl` service status changes
      - This is why many Arch Linux system administrators handle both packages and services separately
  - Files in the `backup=` array (in `PKGBUILD`) are handled in a special way on package removal or package upgrade
    - This only affects files that have been changed from those shipped
    - `backup=` files are copied to `.pacsave` files in the same directory on removal
    - `backup=` files are ignored on a package upgrade
    - This is different from Debian, which will merely ignore the files, not move altered files to backups
      - This relates to the nature for Arch Linux to be minimalist, part of its appeal to some developers
  - We don't need to use the `-s` flag with `makepkg` this time because of the singular dependency issue
    - The `.service` structure needs `systemd`
    - If `systemd` was not already in use, then it could be SysVinit or Upstart, which `systemd` should conflict with
  - The name of the directory containing the package files does not matter
  - `PKGBUILD` is the instruction file, not a directory as might be expected with other package builders
  - `makepkg` must be run from the same directory containing `PKGBUILD`
  - The `.pkg.tar.zst` file will appear inside the containing directory

| **Enable & start services** :$

```console
sudo systemctl enable toplogger
sudo systemctl start toplogger
sudo apparmor_parser -r /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
sudo aa-enforce /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
```

| **Disable & stop services** :$

```console
sudo systemctl stop toplogger
sudo systemctl disable toplogger
sudo aa-disable /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
```

| **Remove Arch package** :$ (optional)

```console
sudo pacman -R toplogger
```

| **Purge Arch package** :$ (optional)

```console
sudo pacman -Rsn toplogger
```

### II. Debian Package (`toplogger.deb`)
*Debian package directory structure:*

| **`deb/`** :

```
deb/
└─ toplogger/
   ├─ DEBIAN/
   │  ├─ conffiles
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
      ├─ apparmor.d/
      │  └─ usr.lib.toplogger.toplogger.sh
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
Maintainer: Ink Is A Verb <codes@inkisaverb.com>
Depends: systemd
Description: top logs per-minute

```

- In `DEBIAN/` create file: `conffiles`

| **`deb/toplogger/DEBIAN/conffiles`** : (retain these `/etc/` configs on package removal)

```
/etc/toplogger/conf
```

- In `DEBIAN/` create file: `postinst`
  - Make it executable with :$ `chmod +x DEBIAN/postinst`

| **`deb/toplogger/DEBIAN/postinst`** :

```
#!/bin/bash

# exit from any errors
set -e

# Create our config that does not reside in the package
echo "/var/log/toplogger  # Directory where logs are sorted and kept" > "/etc/toplogger/logdir"

# Make the loop script executable
chmod +x /usr/lib/toplogger/toplogger.sh

# Service
systemctl daemon-reload
systemctl enable toplogger
systemctl start toplogger

# AppArmor
apparmor_parser -r /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
aa-enforce /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
```

- In `DEBIAN/` create file: `prerm`
  - Make it executable with :$ `chmod +x DEBIAN/prerm`

| **`deb/toplogger/DEBIAN/prerm`** : (disable services after remove)

```
#!/bin/bash

# exit from any errors
set -e

# Service
systemctl stop toplogger
systemctl disable toplogger

# AppArmor
aa-disable /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
```

- In `DEBIAN/` create file: `postrm`
  - Make it executable with :$ `chmod +x DEBIAN/postrm`

| **`deb/toplogger/DEBIAN/postrm`** : (remove `/etc/` configs only on package purge)

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
  - `deb/toplogger/apparmor.d/`
  - `deb/toplogger/usr/lib/toplogger/`
  - `deb/toplogger/usr/lib/systemd/system/`
- Place file `conf` in `deb/toplogger/etc/toplogger/`
- Place file `toplogger.sh` in `deb/toplogger/usr/lib/toplogger/`
- Place file `toplogger.service` in `deb/toplogger/usr/lib/systemd/system/`
- Place file `usr.lib.toplogger.toplogger.sh` in `deb/toplogger/apparmor.d/`
- Build package:
  - Navigate to directory `deb/`
  - Run this, then the package will be built, then installed:

| **Build, *then* install Debian package** :$

```console
dpkg-deb --build toplogger  # Create the .deb package
sudo dpkg -i toplogger.deb  # Install the package
```

- Special notes about Debian
  - `systemctl` will enable, start, stop, or disable the service through the package installation
    - This is because of how `dpkg` handles the packages
    - This handling method is one of the appeals to Debian for some developers
  - Config files are listed in `DEBIAN/conffiles`
    - These files will be ignored on package upgrade or removal
      - Config files will be preserved *even if not changed*, unlike Arch Linux
      - This preserves original files, not moving them to backup copies as with Arch Linux
      - This handling method is one of the appeals to Debian for some developers
    - These files will be removed on package purge
      - Package purge considers both `conffiles` & `postrm`
        - Without `postrm`, removing the package will attempt to remove everything created at install
        - Contents listed in `conffiles` will be left in place without the `--purge` flag for `apt remove`
        - Because we add `/etc/toplogger/logdir` apart from files included with the package, `apt remove --purge` will not delete `/etc/toplogger/` without `postrm` explicitly running `rm -rf /etc/toplogger`
          - Test this by removing the file `DEBIAN/postrm`, rebuild with `dpkg-deb --build`, then `sudo apt remove --purge toplogger`; an error will explain why `/etc/toplogger` was not removed
    - Only files that reside within the package can be listed here
    - The only config file allowed in `conffiles` is `/etc/toplogger/conf`
    - `/etc/toplogger/logdir` is created via `echo`, not residing in the package, so it can't be listed in `conffiles`
  - The script file at `usr/lib/toplogger/toplogger.sh` does not need to be executable
    - This is because this installer uses a `postinst` script
    - This script will set the permissions in the command `chmod +x /usr/lib/toplogger/toplogger.sh`
  - The directory of the package files (`toplogger/`) will be the same as the package installer's `.deb` basename
  - The package installer will appear at `toplogger.deb` in the same directory as (`toplogger/`) regardless of the PWD from where the `dpkg-deb --build` command was run
    - For `deb/toplogger` it will be at `deb/toplogger.deb`

| **Remove Debian package** :$ (optional)

```console
sudo apt-get remove toplogger
```

| **Purge Debian package** :$ (optional)

```console
sudo apt-get remove --purge toplogger
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
      ├─ toplogger.sh
      └─ usr.lib.toplogger.toplogger.sh
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
We are creating the top logger service RPM installer...
Other commands could go here...
####################################################"

%build
# We could put some commands here if we needed to build from source

%install
install -Dm755 "$RPM_SOURCE_DIR/toplogger.sh" "$RPM_BUILD_ROOT/usr/lib/toplogger/toplogger.sh"
install -Dm644 "$RPM_SOURCE_DIR/toplogger.service" "$RPM_BUILD_ROOT/usr/lib/systemd/system/toplogger.service"
install -Dm644 "$RPM_SOURCE_DIR/conf" "$RPM_BUILD_ROOT/etc/toplogger/conf"
install -Dm644 "$RPM_SOURCE_DIR/usr.lib.toplogger.toplogger.sh" "$RPM_BUILD_ROOT/etc/apparmor.d/usr.lib.toplogger.toplogger.sh"

echo "/var/log/toplogger  # Directory where logs are sorted and kept" > "$RPM_BUILD_ROOT/etc/toplogger/logdir"

%post
# Service
systemctl daemon-reload
systemctl enable toplogger
systemctl start toplogger

# AppArmor
apparmor_parser -r /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
aa-enforce /etc/apparmor.d/usr.lib.toplogger.toplogger.sh

%preun
if [ $1 -eq 0 ]; then
  # Service
  systemctl stop toplogger
  systemctl disable toplogger
  systemctl daemon-reload

  # AppArmor
  aa-disable /etc/apparmor.d/usr.lib.toplogger.toplogger.sh
fi

%postun
if [ $1 -eq 0 ]; then
  rm -rf /etc/toplogger
fi

%files
/usr/lib/toplogger/toplogger.sh
/usr/lib/systemd/system/toplogger.service
/etc/apparmor.d/usr.lib.toplogger.toplogger.sh

%config(noreplace)
/etc/toplogger/conf
/etc/toplogger/logdir

%changelog
-------------------------------------------------------------------
Thu Jan 01 00:00:00 UTC 1970 codes@inkisaverb.com
- Something started, probably with v1.0.0-1
```

- Create directory: `rpm/rpmbuild/SOURCES/`
- Place files `conf`, `toplogger.sh`, `toplogger.service` & `usr.lib.toplogger.toplogger.sh` in directory `rpm/rpmbuild/SOURCES/`
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
  - `systemctl` will enable, start, stop, or disable the service through the package installation
    - This is because of how `rpm` handles the packages
  - RPM requires the build be done from `~/rpmbuild/`
  - The resulting `.rpm` fill will be at: `~/rpmbuild/RPMS/noarch/toplogger-1.0.0-1.noarch.rpm`
    - This file might actually have a different name, but should be in the same directory (`~/rpmbuild/RPMS/noarch/`)
  - `noarch` means it works on any architecture
    - This part of the filename was set in the `.spec` file with `BuildArch: noarch`
  - Config files listed in the `.spec` file under `%config(noreplace)` should not also be listed under `%files`
  - Some `.spec` file variables could have interchangable names:
    - `$RPM_SOURCE_DIR` = `%{_sourcedir}`
    - `$RPM_BUILD_ROOT` = `%{buildroot}`
    - `$RPM_SOURCE_DIR` & `$RPM_BUILD_ROOT` are "officially" supported
    - Which one you use can make a difference, depending on other things done in the `.spec` file
  - Purge and config preservation are are handled automatically, so there is no separate option for "purge"
    - Configs listed in the `.spec` file under `%config(noreplace)` have no guarantee of being preserved on package removal
      - These are listed here to protect them during package updates, not package removal
    - To overwrite preserved configs on a re-install, use `install -f` for "force" when installing again
  - The `%changelog` is for OpenSUSE's `zypper`
    - RedHat/CentOS may want the date line like this:
      - `* Thu Jan 01 1970 Ink Is A Verb <codes@inkisaverb.com> - 1.0.0-1`

| **Remove RedHat/CentOS package** :$ (optional)

```console
sudo dnf remove toplogger
```

| **Remove OpenSUSE package** :$ (optional)

```console
sudo zypper remove toplogger
```