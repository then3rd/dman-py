#!virtualenv/bin/python
##This code is incomplete. Use at own risk.
#TODO: re-architect so there's client-side timekeeping if the server becomes unavailable

import requests
import json
import uuid
import ConfigParser
import sys
import argparse
import psutil
import os
import subprocess

defuser="foo"
defpass="bar"

Config = ConfigParser.RawConfigParser()
Configfile = "./dman.cfg"

global dman
dman = {}

#DMAN defaults. To be written to Configfile if one doesn't exist.
dman["user"] = "foo"
dman["pass"] = "bar"

#If you change this value, you MUST modify "PATH=/opt/dman:" in autodecrypt.sh
dman["root"] = "/opt/dman/"

#domain+scriptname to query
dman["url"] = "http://localhost:5000/dman"

#Default deadman set timeout.
dman["deftimeout"] = "86400" #24 hours

##Name of encrypted LUKS device (i"m using LVM)
dman["luksopen"] = "/dev/system/encrypted_luks"

#name of cryptsetup luksopen device to be created (/dev/mapper/decryptedname)
dman["luksdecrypt"] = "/dev/mapper/decrypted_luks" 

#Location to mount decrypted device
dman["mountdir"] = "/mnt/decryptmount/"

def Config_write():
    Config.add_section("main")
    dman["uuid"] = uuid.uuid4()
    for x in dman:
        print(x,dman[x])
        Config.set("main", x, dman[x])
    Config.add_section("dirs")
    Config.set("dirs", "dir1", "/foo/bar")
    try:
        with open(Configfile, "wb") as file:
            Config.write(file)
            print("OK: wrote default config: %s") % Configfile
            return True
    except:
        print("ERROR: failed to write config %s") % Configfile 
        raise

def Config_read():
    Config.read(Configfile)
    global ConfigMain
    global ConfigDirs
    try:
        ConfigMain = ConfigSectionMap("main")
        ConfigDirs = ConfigSectionMap("dirs")
        return True
    except:
        print("ERROR: Configfile incomplete")
        raise

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def killthings():
    killpids = set()
    try:
        for proc in psutil.process_iter():
            lsof = proc.open_files()
            for l in lsof:
                for d in ConfigDirs:
                    if l[0].startswith(ConfigDirs[d]):
                        print(proc.pid,ConfigDirs[d])
                        killpids.add(proc.pid)
            for d in ConfigDirs:
                if proc.cwd().startswith(ConfigDirs[d]):
                    print(proc.pid,proc.cwd())
                    killpids.add(proc.pid)
    except:
        print("error, could not read process list. Run as root?")
    for p in killpids:
        try:
            if psutil.Process(p).is_running():
                psutil.Process(p).kill()
                print("killed: %d") % p
        except:
            print("ERROR: failed to kill %d") % p
    #Unmount Directories
    try:
        for d in ConfigDirs:
            subprocess.check_call([ "umount", ConfigDirs[d] ])
            print("OK: unmounted %s") % ConfigDirs[d]
    except:
        print("ERROR: failed to unmount %s") % ConfigDirs[d]
    #Stop LUKS volume
    try:
        subprocess.check_call([ "cryptsetup", "close", ConfigMain["luksdecrypt"] ])
    except:
        print("ERROR: failed to stop LUKS device %s") % ConfigMain["luksdecrypt"] 

def main():
    #Read Config, otherwise attempt to write a re-read a default one.
    try:
        Config_read()
        print("OK: Read existing config.")
    except:
        print("ERROR: Could not read existing config. Creating new...")
        try:
            Config_write()
            try:
                Config_read()
                print("OK: Read new config.")
            except:
                print("ERROR: Could not read new config. What??.")
        except:
            print("ERROR: Could not write new config.")

    #try:
    #    Config_read()
    #except:
    #    print("ERROR: Could not read new config.")

    parser = argparse.ArgumentParser(description="dman client")

    parser.add_argument("-po", "--post",
                        dest="postvar",
                        nargs="?",
                        const=ConfigMain["uuid"],
                        type=str,
                        help="Create new record")

    parser.add_argument("-t", "--time",
                        dest="timevar",
                        nargs="?",
                        const=ConfigMain["deftimeout"],
                        type=int,
                        help="Specify time for post/put")

    parser.add_argument("-g", "--get",
                        action="store_true", dest="getvar",
                        default=False,
                        help="get single record")

    parser.add_argument("-pu", "--put",
                        dest="putvar",
                        nargs="?",
                        const=ConfigMain["deftimeout"],
                        type=int,
                        help="Update existing record")

    parser.add_argument("-a", "--getall",
                        action="store_true", dest="getall",
                        default=False,
                        help="List all records")

    parser.add_argument("-d", "--delete",
                        dest="delete",
                        nargs="?",
                        const=ConfigMain["uuid"],
                        type=str,
                        help="delete current or specified record")

    parser.add_argument("-k", "--kill",
                        action="store_true", dest="kill",
                        default=False)

    args, leftovers = parser.parse_known_args()
    if args.kill:
        killthings()
        sys.exit(0)
        #TODO: report successful kill to server
    if args.timevar is not None:
        time = args.timevar
    else:
        time = ConfigMain["deftimeout"]
    if args.postvar:
        r = requests.post(ConfigMain["url"], data = {"uuid":"%s" % args.postvar, "delta":"%d" % int(time)}, auth=(ConfigMain["user"], ConfigMain["pass"]))
    if args.getvar:
        r = requests.get(ConfigMain["url"] + "/" + ConfigMain["uuid"], auth=(ConfigMain["user"], ConfigMain["pass"]))
        if r.status_code == 404: #bad response, node doesn"t exist yet
            print("Creating new node")
            r = requests.post(ConfigMain["url"], data = {"uuid":"%s" % ConfigMain["uuid"], "delta":"%d" % int(time)}, auth=(ConfigMain["user"], ConfigMain["pass"]))
        else: #good response, node exists
            try:
                j = json.loads(r.text)
                if j["state"] == "alive":
                    print("ALIVE!!")
                elif j["state"] == "dead":
                    print("DEAD :(")
                    killthings()
                else:
                    print("exception")
            except ValueError:
                print("No JSON returned")
    elif args.putvar is not None:
        r = requests.put(ConfigMain["url"] + "/" + ConfigMain["uuid"], data = { "delta":"%d" % int(time) }, auth=(ConfigMain["user"], ConfigMain["pass"]))
    elif args.getall:
        r = requests.get(ConfigMain["url"], auth=(ConfigMain["user"], ConfigMain["pass"]))
    elif args.delete:
        r = requests.delete(ConfigMain["url"] + "/" + args.delete, auth=(ConfigMain["user"], ConfigMain["pass"]))
    else:
        print("Options not specified")

    try:
        r
        print("---JSON---")
        j = json.loads(r.text)
        print(json.dumps(j, indent=4))
    except:
        print("No response or json not loaded")

main()