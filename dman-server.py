#!virtualenv/bin/python
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from flask_httpauth import HTTPBasicAuth
import time
import json
import sys



app = Flask(__name__)
app.config['ERROR_404_HELP'] = False
api = Api(app)
auth = HTTPBasicAuth()
parser = reqparse.RequestParser()
parser.add_argument('state')
parser.add_argument('uuid')
parser.add_argument('delta', type=int)

jsondb = 'dman.json'

NODELIST = {}

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

#Tries to read json file, creates an empty one if not exists.
def readjson():
    global NODELIST
    try:
        #file = open(jsondb, 'r+')
        #NODELIST = json.load(file)
        with open(jsondb) as data_file:    
            NODELIST = json.load(data_file)
    except IOError:
        file = open(jsondb, 'w')
        json.dump(NODELIST, file)
    #print NODELIST

#Writes current nodelist to file
def writejson():
    #print NODELIST
    with open(jsondb, 'w') as outfile:
        json.dump(NODELIST, outfile)

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
    #print args['delta']
    if args['delta']:
        future_epoch = time_plus_delta(args['delta'])
    elif NODELIST[node_uuid]['death']:
        future_epoch = int(NODELIST[node_uuid]['death'])
    else:
        future_epoch = int(time.time())

    node_state = checktimedelta(future_epoch)
    deathcount = future_epoch - int(time.time())
    NODELIST[node_uuid] = {'state': '%s' % node_state, 'death': '%d' % future_epoch, 'count': '%d' % deathcount}
    #print NODELIST
    writejson()

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
        writejson()
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
        #print node_uuid
        checknode(node_uuid)
        return NODELIST[node_uuid], 201

@auth.get_password
def get_password(username):
    if username == 'foo':
        return 'bar'
    return None

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return "Access Not Authorized"
    #return make_response(jsonify({'error': 'Unauthorized access'}), 403)

api.add_resource(DeadmanRoot, '/dman')
api.add_resource(DeadmanNode, '/dman/<node_uuid>')

readjson()

if __name__ == '__main__':
    app.run(debug=True)