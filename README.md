# dman - a python deadman switch

## Installation/Configuration

First install python-devel (or python-dev) for your distribution. It's required for building the psutil module for dman-client.
```
zypper install python-devel
aptitude install python-dev
```

Clone and install client/server
```
cd /opt
git clone https://github.com/then3rd/dman-py.git
cd dman-py
virtualenv venv
venv/bin/pip install -r requirements.txt
chmod +x dman*.py
```

Initialize server user database
```
./dman-server.py -u foo -p bar
  adding or updating "foo" in userdb.json
./dman-server.py -l
  foo : pbkdf2:sha256:50000$xu3ouzGc$21c1f778f881bf36c2873e7e7abee55c21c34806861aa7d7d1f284489a4c4df0
```

Initialize client config then edit as needed
```
./dman-client.py -a
vim dman.cfg
```

Now run the server
```
./dman-server.py
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
  * Restarting with stat
  * Debugger is active!
  * Debugger PIN: 301-067-351
```

Now post a new node
```
./dman-client.py -po
  OK: Read existing config.
  ---JSON---
  {
      "count": "86400",
      "state": "alive",
      "death": "1489274663"
  }
```

Add the following line to root's crontab ( `sudo crontab -e`). When count == 0, proceses are killed, volume unmounted, and luks device will be closed
```
* * * * * /opt/dman/dman-client.py -g >>/opt/dman/dman_l.log 2>&1
```

## Automount configuration

Generate a 2048 bit key
```
dd if=/dev/urandom of=my_secretkey bs=2048 count=1
```

Copy your key into free space on the flash drive. This skips the first 2048 bytes, and places it after the partition table. You may want to zero out and dump the beginning of a freshly partitioned/formatted drive and review/verify that nothing important will be overwritten
```
# dd if=my_secretkey of=/dev/sdb bs=2048 seek=1
```

Get the serial ( `ATTRS{serial}==` ) attribute from your falsh drive.
```
udevadm info -a -n /dev/sdb
```

Modify udev rules to include your serial number and move it to udev rules directory. Multiple devices can be added as separate rules.
```
vim 99-unlock-luks-udev.rules
cp 99-unlock-luks-udev.rules /etc/udev/rules.d/
```

Set `MountFlags=shared` in `/usr/lib/systemd/system/systemd-udevd.service` or the mount command in autodecrypt.sh will fail

Reload udev rules
```
udevadm control --reload-rules
systemctl restart systemd-udevd.service
```

Modify `autodecrypt.sh` to suit your environment. You should now have automatic luksOpen/mount functionality when plugging in the USB device containing the key.

##TODO

TODO: Write a project description

TODO: Impliment client-side timekeeping

TODO: replace autodecrypt.sh with python in dman-client