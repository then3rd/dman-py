# dman - a python deadman switch
TODO: Write a project description


## Server Installation/Config
TODO

## Server Usage
TODO

## Client Installation/Config

First. You will need to get the serial ( `ATTRS{serial}==` ) attribute from your falsh drive. Multiple devices can be added as separate rules.
```
# udevadm info -a -n /dev/sdb
```

Modify `99-unlock-luks-udev.rules` to include your serial number and copy it to `/etc/udev/rules.d/`

Reload udev
```
# udevadm control --reload-rules
# systemctl restart systemd-udevd.service
```

Generate a 2048 bit key
```
# dd if=/dev/urandom of=my_secretkey bs=2048 count=1
```

Copy your key into free space on the flash drive. This skips the first 2048 bytes, and places it after the partition table. You may want to zero out and dump the beginning of a freshly partitioned/formatted drive and review/verify that nothing important will be overwritten
```
# dd if=my_secretkey of=/dev/sdb bs=2048 seek=1
```

Set `MountFlags=shared` in `/usr/lib/systemd/system/systemd-udevd.service` or the mount command in autodecrypt.sh will fail

Copy scripts to client
```
TODO
```

Modify `dman-client-config.sh` to suit your environment.

Add the following line to root's crontab ( `sudo crontab -e`).
```
* * * * /opt/dman/dman-client.py >>/opt/dman/dman_l.log 2>&1
```

## History
## License

