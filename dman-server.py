#!virtualenv/bin/python
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import time
import json
import sys
import argparse

app = Flask(__name__)
app.config['ERROR_404_HELP'] = False
api = Api(app)
auth = HTTPBasicAuth()
parser = reqparse.RequestParser()
parser.add_argument('state')
parser.add_argument('uuid')
parser.add_argument('delta', type=int)

nodedb = 'nodedb.json'
userdb = 'userdb.json'

NODELIST = {}
USERLIST = {}

#NODELIST = {
#    "b4369235-baae-4eec-99ad-3315b375efc8": {
#        "count": "86400",
#        "state": "alive",
#        "death": "1488420412"
#    },
#    "682010c0-b9d7-4c72-8ead-755824580fb8": {
#        "count": "-6000",
#        "state": "dead", 
#        "death": "1488419905"
#    }
#}

#USERLIST = {
#    "user1": {
#         "pass": generate_password_hash("test123") 
#    }
#    "user2": {
#         "pass": generate_password_hash("test123") 
#    }
#}

#Tries to read json file, creates an empty one if not exists.
def readjson(vfile):
    try:
        with open(vfile) as data_file:    
            return json.load(data_file)
    except IOError:
        writejson(vfile,{})

#Writes current nodelist to file
def writejson(vfile, vlist):
    with open(vfile, 'w') as outfile:
        json.dump(vlist, outfile)

def abort_if_node_doesnt_exist(node_uuid):
    if node_uuid not in NODELIST:
        abort(404, message="Not found")

#adds timer delta to current epoch time
def time_plus_delta(delta):
    ct = int(time.time())
    ft = ct + delta
    #print("%d + %d + %d" % (ct, delta, ft))
    return ft

#checks if current time has exceeded timer delta
def checktimedelta(vtime):
    ct = int(time.time())
    if ct < vtime:
        return "alive"
    else:
        return "dead"

##Checks epoch times and updates the json file
def checknode(node_uuid):
    args = parser.parse_args()
    if args['delta']:
        future_epoch = time_plus_delta(args['delta'])
    elif NODELIST[node_uuid]['death']:
        future_epoch = int(NODELIST[node_uuid]['death'])
    else:
        future_epoch = int(time.time())

    node_state = checktimedelta(future_epoch)
    deathcount = future_epoch - int(time.time())
    NODELIST[node_uuid] = {'state': '%s' % node_state, 'death': '%d' % future_epoch, 'count': '%d' % deathcount}
    writejson(nodedb,NODELIST)

#GET/DELETE/PUT new single items
class DeadmanNode(Resource):
    @auth.login_required
    def get(self, node_uuid):
        abort_if_node_doesnt_exist(node_uuid)
        checknode(node_uuid)
        return NODELIST[node_uuid]

    @auth.login_required
    def delete(self, node_uuid):
        abort_if_node_doesnt_exist(node_uuid)
        del NODELIST[node_uuid]
        writejson(nodedb,NODELIST)
        return '%s deleted' % node_uuid, 201 #204

    @auth.login_required
    def put(self, node_uuid):
        abort_if_node_doesnt_exist(node_uuid)
        args = parser.parse_args()
        checknode(node_uuid)
        return NODELIST[node_uuid], 201

# shows a list of all NODELIST, and lets you POST to add new nodes
class DeadmanRoot(Resource):
    @auth.login_required
    def get(self):
        for i in NODELIST:
            checknode(i)
        return NODELIST

    @auth.login_required
    def post(self):
        args = parser.parse_args()
        node_uuid = args['uuid']
        checknode(node_uuid)
        return NODELIST[node_uuid], 201

@auth.verify_password
def verify_password(username, password):
    if USERLIST[username]:
        return check_password_hash(USERLIST[username]['pass'], password)
    return False

@auth.get_password
def get_password(username):
    if username == 'foo':
        return 'bar'
    return None

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    return "Access Not Authorized"
    #return make_response(jsonify({'error': 'Unauthorized access'}), 403)

def main():
    if __name__ == '__main__':
        api.add_resource(DeadmanRoot, '/dman')
        api.add_resource(DeadmanNode, '/dman/<node_uuid>')

        global NODELIST
        global USERLIST

        NODELIST = readjson(nodedb)
        USERLIST = readjson(userdb)

        #print NODELIST
        #print USERLIST

        parser = argparse.ArgumentParser(description="Deadman Server")
        group = parser.add_argument_group('new user')
        group.add_argument("-u", "--user",
                            dest="user",
                            nargs='?',
                            type=str)
        group.add_argument("-p", "--pass",
                            dest="userpass",
                            nargs='?',
                            type=str)

        parser.add_argument("-d", "--del",
                            action="store_true",
                            default=False,
                            dest="deluser")

        parser.add_argument("-l", "--list",
                            action="store_true",
                            default=False,
                            dest="listuser")

        args, leftovers = parser.parse_known_args()

        if args.listuser:
            for k,v in USERLIST.items():  # `items()` for python3 `iteritems()` for python2
                print("%s : %s") % (k, USERLIST[k]['pass'])
        else:
            if args.user:
                if args.deluser:
                    try:
                        del USERLIST[args.user]
                        writejson(userdb,USERLIST)
                        print 'user %s deleted' % args.user
                    except:
                        print("user does not exist")
                else:
                    if args.userpass:
                        print('adding or updating "%s" in %s') % (args.user, userdb)
                        appenduser = { 'pass' : generate_password_hash(args.userpass) }
                        USERLIST[args.user] = appenduser
                        writejson(userdb,USERLIST)
                    else:
                        print "password required"
            else:
                app.run(debug=True)

main()