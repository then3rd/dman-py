#!virtualenv/bin/python
##This code is incomplete. Use at own risk.

import requests
import json
import uuid
import ConfigParser
import sys
import argparse

defuser='foo'
defpass='bar'

config = ConfigParser.RawConfigParser()
configfile = './dman.cfg'

#DMAN
#If you change this value, you MUST modify 'PATH=/opt/dman:' in autodecrypt.sh
dmanroot = "/opt/dman/"

#domain+scriptname to query
dmanurl = 'http://localhost:5000/dman'

#Default deadman set timeout.
deftimeout = '86400' #24 hours

##Name of encrypted LUKS device (i'm using LVM)
luksopen = "/dev/system/encryptedvolume"

#name of cryptsetup luksopen device to be created (/dev/mapper/decryptedname)
decryptdir = "decryptedname" 

#Location to mount decrypted device
mountdir = "/mnt/decryptmount/"

vdeftimeout = 0

def config_write():
    config.add_section('main')
    vuuid = uuid.uuid4()
    config.set('main', 'uuid', '%s' % vuuid)
    config.set('main', 'user', '%s' % defuser)
    config.set('main', 'pass', '%s' % defpass)
    config.set('main', 'dmanroot', '%s' % dmanroot)
    config.set('main', 'dmanurl', '%s' % dmanurl)
    config.set('main', 'deftimeout', '%s' % deftimeout)
    config.set('main', 'luksopen', '%s' % luksopen)
    config.set('main', 'decryptdir', '%s' % decryptdir)
    config.set('main', 'mountdir', '%s' % mountdir)
    with open(configfile, 'wb') as file:
        config.write(file)
    print "wrote default config: %s" % configfile
    return True

def config_read():
    config.read(configfile)
    global vuuid
    global vuser
    global vpass
    global vdmanroot
    global vdmanurl
    global vdeftimeout
    global vluksopen
    global vdecryptdir
    global vmountdir
    vuuid = config.get('main', 'uuid')
    vuser = config.get('main', 'user')
    vpass = config.get('main', 'pass')
    vdmanroot = config.get('main', 'dmanroot')
    vdmanurl = config.get('main', 'dmanurl')
    vdeftimeout = config.getint('main', 'deftimeout')
    vluksopen = config.get('main', 'luksopen')
    vdecryptdir = config.get('main', 'decryptdir')
    vmountdir = config.get('main', 'mountdir')
    print(configfile + ' loaded')
    #print(vuuid)
    return True

def killthings():
    print('lsof "%s" 2>/dev/null|awk \'{if ($2 ~ /^[0-9]/) print $2}\'|xargs kill' % vmountdir)
    print('umount "%s"' % vmountdir)
    print('cryptsetup close "%s"' % vdecryptdir)

def main():
    #Read config, otherwise attempt to write a re-read a default one.
    global vdeftimeout
    try:
        config_read()
    except:
        try:
            config_write()
            config_read()
        except:
            "cound not write config!"

    parser = argparse.ArgumentParser(description="dman client")

    parser.add_argument("-po", "--post",
                        dest="postvar",
                        nargs='?',
                        const=vuuid,
                        type=str)

    parser.add_argument("-g", "--get",
                        action="store_true", dest="getvar",
                        default=False)

    parser.add_argument("-pu", "--put",
                        dest="putvar",
                        nargs='?',
                        const=vdeftimeout,
                        type=int)

    parser.add_argument("-a", "--getall",
                        action="store_true", dest="getall",
                        default=False)

    parser.add_argument("-d", "--delete",
                        dest="delete",
                        nargs='?',
                        const=vuuid,
                        type=str)

    args, leftovers = parser.parse_known_args()

    if args.postvar:
        response = requests.post(vdmanurl, data = {'uuid':'%s' % args.postvar, 'delta':'%d' % vdeftimeout}, auth=(vuser, vpass))
    if args.getvar:
        response = requests.get(vdmanurl + "/" + vuuid, auth=(vuser, vpass))
        #print response.status_code
        if response.status_code == 404: #bad response, node doesn't exist yet
            print "Creating new node"
            response = requests.post(vdmanurl, data = {'uuid':'%s' % vuuid, 'delta':'%d' % vdeftimeout}, auth=(vuser, vpass))
        else: #good response, node exists
            try:
                json_object = json.loads(response.text)
                if json_object["state"] == "alive":
                    print("ALIVE!!")
                elif json_object["state"] == "dead":
                    print("DEAD :(")
                    killthings()
                else:
                    print("exception")
            except ValueError:
                print("No JSON returned")
    elif args.putvar:
        response = requests.put(vdmanurl + "/" + vuuid, data = { 'delta':'%d' % args.putvar }, auth=(vuser, vpass))
    elif args.getall:
        response = requests.get(vdmanurl, auth=(vuser, vpass))
    elif args.delete:
        response = requests.delete(vdmanurl + "/" + args.delete, auth=(vuser, vpass))
    else:
        print("Options not specified")

    try:
        response
        print("---JSON---")
        json_object = json.loads(response.text)
        print json.dumps(json_object, indent=4)
    except:
        print("No response or json_object loaded")

main()