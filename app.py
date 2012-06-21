import re, os, inspect, sys, datetime
from functools import wraps

thisPath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/'
if thisPath == '/':
    thisPath = './'
sys.path.append(thisPath+'libs/')

from flask import Flask, Response, redirect, \
        url_for, request, session, abort, \
        render_template, json, jsonify

# Google App Engine Block
try:
    import logging
    from google.appengine.api import \
            mail, users
    from google.appengine.ext.webapp.util import \
            run_wsgi_app
    from google.appengine.ext import \
            db
    run_on_google = True
except:
    run_on_google = False
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
        'wmiller@hbuhsd.edu',
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
        'wmiller@hbuhsd.edu',
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

class Support_Ticket(db.Model):
    ticket_type = db.StringProperty()
    user_type = db.StringProperty()
    site = db.StringProperty()
    macro = db.StringProperty()
    micro = db.StringProperty()
    
    submitted_on = db.DateTimeProperty(auto_now_add=True)
    submitted_by = db.UserProperty()
    
    closed = db.BooleanProperty()
    completed_on = db.DateTimeProperty()
    completed_by = db.UserProperty()
    completed_meta = db.StringListProperty()

    assigned_to = db.StringProperty()
    invited = db.StringListProperty()
    description = db.StringProperty()

    elevated = db.BooleanProperty()
    elevated_on = db.DateTimeProperty()
    elevated_by = db.UserProperty()
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
    submitted_by = db.UserProperty()
    assigned_to = db.StringProperty()

def ticket_to_json(ticket):
    this_ticket = {
            'type': ticket.ticket_type,
            'user_type': ticket.user_type,
            'site': ticket.site,
            'macro': ticket.macro,
            'micro': ticket.micro,
            'submitted_on': str(ticket.submitted_on)[:16],
            'submitted_by': str(ticket.submitted_by),
            'closed': ticket.closed,
            'completed_on': str(ticket.completed_on)[:16],
            'completed_by': str(ticket.completed_by),
            'assigned_to' : str(ticket.assigned_to),
            'description' : ticket.description,
            'elevated': ticket.elevated,
            'elevated_on': str(ticket.elevated_on)[:16],
            'elevated_by': str(ticket.elevated_by),
            'elevated_reason': ticket.elevated_reason,
            'starred': ticket.starred,
            'priority': ticket.priority,
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
        'submitted_by': str(note.submitted_by),
        'submitted_on': str(note.submitted_on)[:16],
        'assigned_to': assigned_to,
        }
    return this_note

def permissions(dbItem, user):
    if user in ADMINS:
        return True
    else:
        if dbItem.submitted_by == user or \
                str(dbItem.assigned_to) == user or \
                dbItem.assigned_to == None:
            return True
        else:
            return False

def get_my_tickets(user):
    if str(user) in ADMINS:
        my_tickets = Support_Ticket.all()
    elif str(user) in ETS:
        my_tickets = Support_Ticket.gql(
                "WHERE elevated = TRUE")
    else:
        my_tickets = Support_Ticket.gql(
                "WHERE submitted_by = :submitted_by",
                submitted_by=user)
        my_tickets.update(Support_Ticket.gql(
            "WHERE assigned_to = :assigned_to",
            assigned_to=str(user)))
    return my_tickets

@app.route('/')
def home():
    if run_on_google:
        logging.info(users.get_current_user())
        this_user = str(users.get_current_user())
        if not re.match('.*@.*', this_user):
            this_user += '@hbuhsd.edu'
    else:
        this_user = 'test@hbuhsd.edu'

    page_params['title'] = 'Ticket Manager'
    page_params['message'] = 'tickets displayed are for user %s' % this_user
    page_params['user_name'] = this_user

    return render_template('manage_tickets.html', page_params=page_params)

@app.route('/new_ticket', methods=['POST', 'GET', 'PUT', 'DELETE'])
def new_ticket():
    if run_on_google:
        logging.info(users.get_current_user())
        this_user = str(users.get_current_user())+'@hbuhsd.edu'
    else:
        this_user = 'test@hbuhsd.edu'

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
                submitted_by=users.get_current_user(),
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

@app.route('/note/<note_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def note(note_id):
    this_user = str(users.get_current_user())
    these_params = request.json
    if note_id == 'new' and request.method == 'POST':
        this_ticket = Support_Ticket.get_by_id(int(these_params['for_ticket']))
        if (this_ticket.elevated and this_user in ETS) or permissions(this_ticket, this_user):
            if 'assigned_to' not in these_params:
                these_params['assigned_to'] = None
            Note(for_ticket=this_ticket,
                    message=these_params['message'],
                    assigned_to=these_params['assigned_to'],
                    submitted_by=users.get_current_user()).put()
            return JSON_OK
        else:
            return JSON_ERROR

    if request.method == 'GET':
        this_note = Note.get_by_id(int(note_id))
        if permissions(this_note, this_user):
            return Response(
                    response=json.dumps(
                    note_to_json(this_note)),
                    mimetype="application/json")
        else:
            return JSON_ERROR
    elif request.method == 'DELETE':
        this_note = Note.get_by_id(int(note_id))
        if str(this_note.submitted_by) == this_user:
            this_note.delete()
            return JSON_OK
        else:
            return JSON_ERROR

@app.route('/notes/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def notes(ticket_id):
    this_user = str(users.get_current_user())
    logging.info('notes request for ticket_id: %s' % int(ticket_id))
    this_ticket = Support_Ticket.get_by_id(int(ticket_id))
    these_notes = [note_to_json(note) for note in this_ticket.notes if
            (permissions(note, this_user) or (permissions(note, this_user) and this_ticket.elevated and this_user in ETS))]
    return Response(
            response=json.dumps(these_notes),
            mimetype="application/json")

# POST = create # PUT = update # GET = retrieve # DELETE = delete # Backbone.js
@app.route('/ticket/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def ticket(ticket_id):
    this_user = str(users.get_current_user())
    if request.method == 'GET':
        this_ticket = Support_Ticket.get_by_id(int(ticket_id))
        if permissions(this_ticket, this_user):
            return Response(
                    response=json.dumps(ticket_to_json(this_ticket)),
                    mimetype="application/json")
    elif request.method == 'PUT':
        these_params = request.json
        this_ticket = Support_Ticket.get_by_id(int(ticket_id))
        if permissions(this_ticket, this_user):

            # Handle ticket close
            if not this_ticket.closed and these_params['closed']:
                if not these_params['completed_meta']:
                    these_params['completed_meta'] = []
                this_ticket.closed = True
                this_ticket.completed_on = datetime.datetime.now()
                this_ticket.completed_by = users.get_current_user()
                this_ticket.completed_meta = these_params['completed_meta']

            # Handle ticket elevation
            if not this_ticket.elevated and these_params['elevated']:
                if not these_params['elevated_reason']:
                    these_params['elevated_reason'] = ''
                this_ticket.elevated = True
                this_ticket.elevated_on = datetime.datetime.now()
                this_ticket.elevated_by = users.get_current_user()
                this_ticket.elevated_reason = these_params['elevated_reason']

            this_ticket.starred = these_params['starred']
            this_ticket.put()
            return JSON_OK
    else:
        return JSON_ERROR

@app.route('/tickets', methods=['GET'])
def tickets():
    this_user = users.get_current_user()
    my_tickets = get_my_tickets(this_user)
    these_tickets = [ticket_to_json(ticket) for ticket in my_tickets]

    return Response(
            response=json.dumps(these_tickets),
            mimetype="application/json")

@app.route('/test', methods=['POST', 'GET', 'PUT', 'DELETE'])
def test():
    return jsonify({'message': 'OK'})

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
    if run_on_google == False:
        app.run(
                debug=True,
                host='0.0.0.0',
                port=5000,
                )
    else:
        run_wsgi_app(app)
