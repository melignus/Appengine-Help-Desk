import re, os, inspect, sys, datetime, urllib, urllib2
from functools import wraps

thisPath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/'
if thisPath == '/':
    thisPath = './'
sys.path.append(thisPath+'libs/')

from flask import Flask, Response, redirect, \
        url_for, request, session, abort, \
        render_template, json, jsonify

# Google App Engine Block
import logging
from google.appengine.api import \
        mail, users, channel
from google.appengine.ext.webapp.util import \
        run_wsgi_app
from google.appengine.ext import \
        db
# End Google App Engine Block

SITES = [
        'DIST',
        'WHS',
        'EHS',
        'FVHS',
        'MHS',
        'OVHS',
        'HBHS',
        'VVHS',
        'HBAS',
        'CDS',
        'CHS',
        'Food Services',
        'Transportation',
        ]

NET_TECHS = {
        'DIST': 'ishelp@hbuhsd.edu',
        'WHS': 'dhidalgo@hbuhsd.edu',
        'EHS': 'ptabony@hbuhsd.edu',
        'FVHS': 'iprotsenko@hbuhsd.edu',
        'MHS': 'rpowell@hbuhsd.edu',
        'OVHS': 'dtran@hbuhsd.edu',
        'HBHS': 'along@hbuhsd.edu',
        'VVHS': 'ishelp@hbuhsd.edu',
        'HBAS': 'wlacap@hbuhsd.edu',
        'CDS': 'wlacap@hbuhsd.edu',
        'CHS': 'wlacap@hbuhsd.edu',
        'Food Services': 'ishelp@hbuhsd.edu',
        'Transportation': 'ishelp@hbuhsd.edu',
        }

IS_HELP = [
        'wbeen@hbuhsd.edu',
        'nbuihner@hbuhsd.edu',
        'mford@hbuhsd.edu',
        'mratanapratum@hbuhsd.edu',
        'dhoang@hbuhsd.edu',
        'djohnson@hbuhsd.edu',
        'greeves@hbuhsd.edu',
        'mtabata@hbuhsd.edu',
        ]

ADMINS = [
        'nbuihner@hbuhsd.edu',
        'mford@hbuhsd.edu',
        'test@example.com',
        #'test1@example.com',
        #'test2@example.com',
        ]

ETS = [
        'test1@example.com',
        'test2@example.com',
        ]

JSON_ERROR = Response(
        response=json.dumps(False),
        mimetype="application/json",
        status=400)

JSON_OK = Response(
        response=json.dumps({}),
        mimetype="application/json")

app = Flask(__name__)

page_params = {}

class User(db.Model):
    firstname = db.StringProperty()
    lastname = db.StringProperty()
    email = db.StringProperty()
    admin = db.BooleanProperty()
    ets = db.BooleanProperty()
    nettech = db.BooleanProperty()
    last_login = db.DateTimeProperty()
    super_admin = db.BooleanProperty()

class Support_Ticket(db.Model):
    ticket_type = db.StringProperty()
    user_type = db.StringProperty()
    site = db.StringProperty()
    macro = db.StringProperty()
    micro = db.StringProperty()
    
    submitted_on = db.DateTimeProperty(auto_now_add=True)
    submitted_by = db.StringProperty()
    submitted_ipaddress = db.StringProperty()
    
    closed = db.BooleanProperty()
    completed_on = db.DateTimeProperty()
    completed_by = db.StringProperty()
    completed_meta = db.StringListProperty()

    assigned_to = db.StringProperty()
    description = db.StringProperty()
    inventory = db.StringProperty()

    elevated = db.BooleanProperty()
    elevated_on = db.DateTimeProperty()
    elevated_by = db.StringProperty()
    elevated_reason = db.StringProperty()

    starred = db.BooleanProperty()
    priority = db.BooleanProperty()
    on_hold = db.BooleanProperty()
    #send_to_todo = db.BooleanProperty()
    #due_date = db.DateTimeProperty()

class Note(db.Model):
    for_ticket = db.ReferenceProperty(Support_Ticket, 
            collection_name='notes')
    message = db.StringProperty()

    submitted_on = db.DateTimeProperty(auto_now_add=True)
    submitted_by = db.StringProperty()
    assigned_to = db.StringProperty()

def fix_time(time):
    try:
        time = time.isoformat()
    except:
        time = False
    return time

def ticket_to_json(ticket):
    this_ticket = {
            'type': ticket.ticket_type,
            'user_type': ticket.user_type,
            'site': ticket.site,
            'macro': ticket.macro,
            'micro': ticket.micro,
            'submitted_on': fix_time(ticket.submitted_on),
            'submitted_by': ticket.submitted_by,
            'closed': ticket.closed,
            'completed_on': fix_time(ticket.completed_on),
            'completed_by': ticket.completed_by,
            'assigned_to' : ticket.assigned_to,
            'description' : ticket.description,
            'elevated': ticket.elevated,
            'elevated_on': fix_time(ticket.elevated_on),
            'elevated_by': ticket.elevated_by,
            'elevated_reason': ticket.elevated_reason,
            'starred': ticket.starred,
            'priority': ticket.priority,
            'on_hold': ticket.on_hold,
            'inventory': ticket.inventory,
            'id': str(ticket.key().id()),
            }
    return this_ticket

def note_to_json(note):
    if note.assigned_to == None:
        assigned_to = False
    else:
        assigned_to = note.assigned_to
    this_note = {
        'id': str(note.key().id()),
        'message': note.message,
        'submitted_by': note.submitted_by,
        'submitted_on': note.submitted_on.isoformat(),
        'assigned_to': assigned_to,
        }
    return this_note

def user_to_json(user):
    this_user = {
            'id': str(user.key().id()),
            'firstname': user.firstname,
            'lastname': user.lastname,
            'email': user.email,
            'last_login': fix_time(user.last_login),
            'ets': user.ets,
            'nettech': user.nettech,
            'admin': user.admin,
            'super_admin': user.super_admin,
            }
    return this_user

#TODO add support for action and fix the rest of the permissions settings
def admin_permissions(user, action):
    if action == 'read':
        this_query = User.gql("WHERE email = :user", user=user)
        if len([user for user in this_query]):
            this_user = this_query[0]
            if this_user.admin or this_user.super_admin:
                return True
    if action == 'update':
        this_query = User.gql("WHERE email = :user", user=user)
        if len([user for user in this_query]):
            this_user = this_query[0]
            if this_user.admin or this_user.super_admin:
                return True
    if action == 'super_admin':
        this_query = User.gql("WHERE email = :user", user=user)
        if len([user for user in this_query]):
            this_user = this_query[0]
            if this_user.super_admin:
                return True
    return False

def ticket_permissions(ticket, user, action):
    if action == 'read':
        if user in ADMINS:
            return True
        elif ticket.assigned_to == user:
            return True
        elif ticket.elevated and user in ETS:
            return True
        else:
            return False
    if action == 'update':
        if user in ADMINS:
            return True
        elif ticket.assigned_to == user:
            return True
        elif ticket.elevated and user in ETS:
            return True
        else:
            return False

def note_permissions(note, user, action):
    if action == 'read':
        if note.submitted_by == user:
            return True
        elif note.assigned_to == user:
            return True
        elif note.for_ticket.elevated and (user in ETS) and not note.assigned_to:
            return True
        else:
            return False
    elif action == 'delete':
        if note.submitted_by == user:
            return True
        else:
            return False
    elif action == 'create':
        if ticket_permissions(note, user, 'update'):
            return True
        else:
            return False
    else:
        return False

def get_my_tickets(user):
    if user in ADMINS:
        my_tickets = Support_Ticket.all()
    elif user in ETS:
        my_tickets = Support_Ticket.gql(
                "WHERE elevated = TRUE")
    else:
        my_tickets = Support_Ticket.gql(
                "WHERE assigned_to = :assigned_to",
                assigned_to=user)
    return my_tickets

@app.route('/')
def home():
    this_user = str(users.get_current_user())
    page_params['user_name'] = this_user

    token = channel.create_channel(this_user)
    page_params['token'] = token

    if 'link' in request.args:
        logging.info('Handle direct link...')

    if this_user in ADMINS:
        return render_template('admin_tickets.html',
                page_params=page_params)
    elif (this_user in [NET_TECHS[k] for k in NET_TECHS]) or (this_user in ETS):
        return render_template('manage_tickets.html', 
                page_params=page_params)
    else:
        return abort(403)

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    this_user = str(users.get_current_user())
    
    if 'GET' in request.method:
        first_time = User.gql("WHERE super_admin = TRUE")
        if not [item for item in first_time]:
            return render_template('first_time.html', page_params=page_params)
        else:
            user = User.gql(
                    "WHERE super_admin = TRUE AND email = :user", user=this_user)
            if user:
                return render_template('admin_panel.html', page_params=page_params)
            else:
                return abort(403)
    elif 'POST' in request.method:
        logging.info(request.form)
        these_params = request.form
        super_admin = User(
                first_name=these_params['first_name'],
                last_name=these_params['last_name'],
                email=these_params['email'],
                super_admin=True,
                )
        super_admin.put()
        return url_for('/admin')

@app.route('/new_ticket', methods=['POST', 'GET', 'PUT', 'DELETE'])
def new_ticket():
    this_user = str(users.get_current_user())

    if request.method == 'POST':
        logging.info(request.form)
        these_params = request.form

        if these_params['site'] in NET_TECHS:
            set_assignment = NET_TECHS[these_params['site']]
        else:
            set_assignment = NET_TECHS['DIST']

        this_ticket = Support_Ticket(
                ticket_type=these_params['type'],
                user_type=these_params['user_type'],
                site=these_params['site'],
                macro=these_params['macro'],
                micro=these_params['micro'],
                description=these_params['description'],
                inventory=these_params['inventory'],
                submitted_by=str(users.get_current_user()),
                submitted_ipaddress=request.remote_addr,
                assigned_to=set_assignment,
                elevated=False,
                closed=False,
                starred=False,
                priority=False,
                on_hold=False,
                )
        this_ticket.put()
        return JSON_OK

    page_params['sites'] = SITES
    page_params['title'] = 'New Ticket'
    page_params['message'] = \
            'please fill all fields to submit a new support ticket'

    return render_template('new_ticket.html', page_params=page_params)

@app.route('/user/<user_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def single_user(user_id):
    these_params = request.json
    this_user = str(users.get_current_user())
    if request.method == 'GET':
        if admin_permissions(this_user, 'read'):
            user = User.get_by_id(int(user_id))
            if user:
                return Response(
                        response=json.dumps(user_to_json(user)),
                        mimetype="application/json")
    elif request.method == 'PUT':
        if admin_permissions(this_user, 'update'):
            user = User.get_by_id(int(user_id))
            if this_query:
                if these_params['firstname'] != user.firstname:
                    user.firstname = these_params['firstname']
                if these_params['lastname'] != user.lastname:
                    user.lastname = these_params['lastname']
                if these_params['email'] != user.email:
                    user.email = these_params['email']
                if these_params['ets'] != user.ets:
                    user.ets = these_params['ets']
                if these_params['nettech'] != user.nettech:
                    user.nettech = these_params['nettech']
                if these_params['admin'] != user.admin and admin_permissions(this_user, 'super_admin'):
                    user.admin = these_params['admin']
                user.put()
                return JSON_OK
    elif request.method == 'DELETE':
        if admin_permissions(this_user, 'update'):
            user = User.get_by_id(int(user_id))
            if user:
                this_query.delete()
                return JSON_OK
    elif user_id == 'new' and request.method == 'POST':
        if admin_permissions(this_user, 'update'):
            new_user = User(
                    email=these_params['email'],
                    firstname=these_params['firstname'],
                    lastname=these_params['lastname'],
                    admin=these_params['admin'],
                    ets=these_params['ets'],
                    nettech=these_params['nettech'],
                    )
            new_user.put()
            return JSON_OK
    return JSON_ERROR

@app.route('/users', methods=['GET'])
def all_users():
    this_user = str(users.get_current_user())
    if admin_permissions(this_user, 'read'):
        this_query = User.gql("WHERE email != :user", user=this_user)
        return Response(
            response=json.dumps([user_to_json(user) for user in this_query]),
            mimetype="application/json")
    else:
        return JSON_ERROR

@app.route('/note/<note_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def note(note_id):
    this_user = str(users.get_current_user())
    these_params = request.json
    if note_id == 'new' and request.method == 'POST':
        this_ticket = Support_Ticket.get_by_id(int(these_params['for_ticket']))
        if not this_ticket:
            return JSON_ERROR
        if note_permissions(this_ticket, this_user, 'create'):
            if 'assigned_to' not in these_params:
                these_params['assigned_to'] = None
            Note(for_ticket=this_ticket,
                    message=these_params['message'],
                    assigned_to=these_params['assigned_to'],
                    submitted_by=str(users.get_current_user())).put()
            return JSON_OK
        else:
            return JSON_ERROR

    if request.method == 'GET':
        this_note = Note.get_by_id(int(note_id))
        if not this_note:
            return JSON_ERROR
        if note_permissions(this_note, this_user, 'read'):
            return Response(
                    response=json.dumps(
                    note_to_json(this_note)),
                    mimetype="application/json")
        else:
            return JSON_ERROR
    elif request.method == 'DELETE':
        this_note = Note.get_by_id(int(note_id))
        if this_note:
            return JSON_ERROR
        if note_permissions(this_note, this_user, 'delete'):
            this_note.delete()
            return JSON_OK
        else:
            return JSON_ERROR

@app.route('/notes/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def notes(ticket_id):
    this_user = str(users.get_current_user())
    logging.info('notes request for ticket_id: %s' % int(ticket_id))
    this_ticket = Support_Ticket.get_by_id(int(ticket_id))
    if not this_ticket:
        return JSON_ERROR
    these_notes = [note_to_json(note) for note in this_ticket.notes if
            note_permissions(note, this_user, 'read')]
    return Response(
            response=json.dumps(these_notes),
            mimetype="application/json")

# POST = create # PUT = update # GET = retrieve # DELETE = delete # Backbone.js
@app.route('/ticket/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def ticket(ticket_id):
    this_user = str(users.get_current_user())
    if request.method == 'GET':
        this_ticket = Support_Ticket.get_by_id(int(ticket_id))
        if not this_ticket:
            return JSON_ERROR
        if ticket_permissions(this_ticket, this_user, 'read'):
            return Response(
                    response=json.dumps(ticket_to_json(this_ticket)),
                    mimetype="application/json")
    elif request.method == 'PUT':
        these_params = request.json
        this_ticket = Support_Ticket.get_by_id(int(ticket_id))
        if not this_ticket:
            return JSON_ERROR
        if ticket_permissions(this_ticket, this_user, 'update'):

            # Handle ticket close and reopen
            if not this_ticket.closed and these_params['closed']:
                if not these_params['completed_meta']:
                    these_params['completed_meta'] = []
                this_ticket.closed = True
                this_ticket.completed_on = datetime.datetime.now()
                this_ticket.completed_by = this_user
                this_ticket.completed_meta = these_params['completed_meta']
                this_ticket.priority = False
            elif this_ticket.closed and not these_params['closed']:
                this_ticket.closed = False

            # Handle ticket elevation and deelevation
            if not this_ticket.elevated and these_params['elevated']:
                if not these_params['elevated_reason']:
                    these_params['elevated_reason'] = ''
                this_ticket.elevated = True
                this_ticket.elevated_on = datetime.datetime.now()
                this_ticket.elevated_by = this_user
                this_ticket.elevated_reason = these_params['elevated_reason']
            elif this_ticket.elevated and not these_params['elevated']:
                this_ticket.elevated = False

            # Handle ticket reassignment
            if this_ticket.assigned_to != these_params['assigned_to'] and \
                    this_user in ADMINS:
                new_assignment = these_params['assigned_to']
                if new_assignment in NET_TECHS or \
                        new_assignment in ETS or \
                        new_assignment in ADMINS:
                    this_ticket.assigned_to = new_assignment
                else:
                    return JSON_ERROR

            # Handle ticket inventory number change
            if this_ticket.inventory != these_params['inventory']:
                this_ticket.inventory = these_params['inventory']

            this_ticket.starred = these_params['starred']
            this_ticket.on_hold = these_params['on_hold']
            if this_user in ADMINS:
                this_ticket.priority = these_params['priority']
            this_ticket.put()
            return JSON_OK
        else:
            return JSON_ERROR
    else:
        return JSON_ERROR

@app.route('/tickets', methods=['GET'])
def tickets():
    this_user = str(users.get_current_user())
    my_tickets = get_my_tickets(this_user)
    these_tickets = [ticket_to_json(ticket) for ticket in my_tickets]

    return Response(
            response=json.dumps(these_tickets),
            mimetype="application/json")

@app.route('/test', methods=['POST', 'GET', 'PUT', 'DELETE'])
def test():
    logging.info('json: %s' % request.json)
    logging.info('form: %s' % request.form)
    logging.info('args: %s' % request.args)
    logging.info('request: %s' % request)
    return jsonify({'message': request.args['code']})

@app.route('/test2', methods=['POST', 'GET', 'PUT', 'DELETE'])
def test2():
    logging.info('json: %s' % request.json)
    logging.info('form: %s' % request.form)
    logging.info('args: %s' % request.args)
    logging.info('request: %s' % request)
    return jsonify({'message': request.args})

@app.route('/test3', methods=['POST', 'GET', 'PUT', 'DELETE'])
def test3():
    try:
        channel.send_message('test@example.com', json.dumps({'message': 'Ok'}))
    except:
        return jsonify({'message': 'Error'})
    return jsonify({'message': 'Ok'})

@app.errorhandler(404)
def page_not_found(error):
    page_params['title'] = '404'
    page_params['message'] = 'The page you are looking for cannot be found'
    return render_template('404.html', page_params=page_params)

@app.errorhandler(403)
def http_forbidden(error):
    page_params['title'] = '403'
    page_params['message'] = \
            'Access to this page is restricted to HBUHSD staff only. To \
            access this page you must have a valid @hbuhsd.edu email account'
    return render_template('403.html', page_params=page_params)

if __name__ == "__main__":
    run_wsgi_app(app)
