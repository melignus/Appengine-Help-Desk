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

ETS = [
        ]

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

def ticket_to_json(ticket):
    this_ticket = {
            'type': ticket.ticket_type,
            'user_type': ticket.user_type,
            'site': ticket.site,
            'macro': ticket.macro,
            'micro': ticket.micro,
            'submitted_on': str(ticket.submitted_on)[:16],
            'submitted_by': str(ticket.submitted_by),
            'completed_on': str(ticket.completed_on)[:16],
            'completed_by': str(ticket.completed_by),
            'assigned_to' : str(ticket.assigned_to),
            'description' : ticket.description,
            'elevated': ticket.elevated,
            'starred': ticket.starred,
            'id': str(ticket.key().id()),
            }
    return this_ticket

def note_to_json(note):
    this_note = {
        'id': str(note.key().id()),
        'message': note.message,
        'submitted_by': str(note.submitted_by),
        'submitted_on': str(note.submitted_on)[:16],
        }
    return this_note

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
                )
        this_ticket.put()
        return jsonify({'message': 'OK'})

    page_params['sites'] = SITES
    page_params['title'] = 'New Ticket'
    page_params['message'] = \
            'please fill all fields to submit a new support ticket'
    return render_template('new_ticket.html', page_params=page_params)

@app.route('/note/<note_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def note(note_id):
    these_params = request.json
    if note_id == 'new' and request.method == 'POST':
        Note(for_ticket=Support_Ticket.get_by_id(int(these_params['for_ticket'])),
                message=these_params['message']).put()
        return Response(
                response=json.dumps({}),
                mimetype="application/json")

    if request.method == 'GET':
        this_note = Note.get_by_id(int(note_id))
        return Response(
                response=json.dumps(
                    note_to_json(this_note)),
                mimetype="application/json")
    elif request.method == 'DELETE':
        this_note = Note.get_by_id(int(note_id))
        this_note.delete()
        return Response(
                response=json.dumps({}),
                mimetype="application/json")

@app.route('/notes/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def notes(ticket_id):
    logging.info('notes request for ticket_id: %s' % int(ticket_id))
    this_query = Support_Ticket.get_by_id(int(ticket_id))
    these_notes = [note_to_json(note) for note in this_query.notes]
    return Response(
            response=json.dumps(these_notes),
            mimetype="application/json")

# POST = create # PUT = update # GET = retrieve # DELETE = delete # Backbone.js
@app.route('/ticket/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def ticket(ticket_id):
    if request.method == 'GET':
        this_query = Support_Ticket.get_by_id(int(ticket_id))
        return Response(
                response=json.dumps({}),
                mimetype="application/json")

    elif request.method == 'PUT':
        these_params = request.json
        this_query = Support_Ticket.get_by_id(int(ticket_id))
        this_query.starred = these_params['starred']
        this_query.put()
        return Response(
                response=json.dumps({}),
                mimetype="application/json")
    else:
        return jsonify({'message': 'ERROR'})

@app.route('/tickets', methods=['GET'])
def tickets():
    this_user = users.get_current_user()
    this_query = Support_Ticket.gql(
            "WHERE submitted_by = :submitted_by",
            submitted_by=users.get_current_user())
    these_tickets = [ticket_to_json(ticket) for ticket in this_query]

    logging.info('this_user: %s requesting_tickets: %s'
            % (this_user, these_tickets))
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
