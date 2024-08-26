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
  rm -rf /var/log/toplogger
fi

%files
/usr/lib/toplogger/toplogger.sh
/usr/lib/systemd/system/toplogger.service
/etc/apparmor.d/usr.lib.toplogger.toplogger.sh

%config(noreplace)
/etc/toplogger/conf
/etc/toplogger/logdir

%changelog
* Thu Jan 01 1970 Ink Is A Verb <codes@inkisaverb.com> - 1.0.0-1
- Something started, probably with v1.0.0-1