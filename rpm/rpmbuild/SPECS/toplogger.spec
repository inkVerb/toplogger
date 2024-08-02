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
# We shouldn't need to create directories that will be created with other install commands, but for ref in dev keep for now
#install -Dm755 "$RPM_BUILD_ROOT/usr/lib/toplogger"
#install -Dm755 "$RPM_BUILD_ROOT/usr/lib/systemd/system"
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