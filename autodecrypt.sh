#!/bin/bash
#TODO: replace this with python in dman-client
PATH=/opt/dman:/sbin:/usr/sbin:/usr/local/sbin:/root/bin:/usr/local/bin:/usr/bin:/bin:/usr/bin/X11:/usr/games:/opt/bin
LUKSOPEN="/dev/system/encrypted_luks"
#name of cryptsetup luksopen device
DECRYPT="/dev/mapper/decrypted_luks" 
#Location to mount decrypted device
MOUNTDIR="/mnt/decryptmount/"
/usr/bin/dd if=/dev/usbkey bs=2048 skip=1 count=1 status=none| /sbin/cryptsetup luksOpen "${LUKSOPEN}" "${DECRYPT}" --key-file=- && /usr/bin/mount /dev/mapper/"${DECRYPT}" "${MOUNTDIR}"
