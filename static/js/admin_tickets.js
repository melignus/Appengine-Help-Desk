var META_LIST = [
    {
        "name": "Alarm Security",
        "types": [
        "CCTV Security",
        "Fire Alarm",
        "Security System",
        ]
    },
    {
        "name": "Audio Visual",
        "types": [
        "Camera",
        "CCTV TV System",
        "DVD",
        "TV",
        "Pro VCR",
        ]
    },
    {
        "name": "Communication",
        "types": [
        "Networking",
        "Network Equipment",
        "Telephone Install",
        "Telephone Repair",
        "Two-Way Radio",
        "Voice Mail Repair",
        ]
    },
    {
        "name": "Computer System",
        "types": [
        "Computer",
        "Computer Upgrade",
        "IT Install Kit",
        "IT Lockdown",
        "Monitor",
        "PC Install Kit",
        "PC Lockdown",
        "Printer",
        ]
    },
    {
        "name": "Office Equipment",
        "types": [
        "Document Reader",
        "Time Stamp",
        "Typewriter",
        ]
    },
    {
        "name": "Pa/Clock",
        "types": [
        "Clock",
        "Local PA",
        "School Main PA",
        ]
    },
    {
        "name": "Projectors",
        "types": [
        "LCD Projector",
        "Overhead Projector",
        "Pole Vault",
        ]
    },
    {
        "name": "Other Equipment",
        "types": [
        "Score Board",
        "Theater Dimming System",
        ]
    },
];

var COMPLETE_META = ["Computer","Printer","Windows","Win95",
    "Win2k","WinXp","WinVista","Win7","Win8","IE","IE6","IE7",
    "IE9","Office","Word","Outlook","Excel","LibreOffice",
    "OpenOffice","Browser","Cookies","History","Icon","Desktop",
    "Reboot","Power Off","Firefox","Chrome","Safari","Opera",
    "Netscape","Mac","Apple","OSX","Tiger","Intel","Dell","HP",
    "Google","Lion","Snow Leopard","SB2000","Citrix","Read180",
    "System44","Plato","Illuminate","Camera","Document Camera",
    "Flash","Java","Virus","Malware","SB2000 Classroom","Google",
    "Gmail","Google Docs","Google Drive","Google Calendar",
    "Google Sites","Scanner","YouTube","Video","Audio CD",
    "Speakers","Sound","Video CD","DVD","Projector","Cable",
    "Ethernet","Wireless","Laptop","PowerSupply","Firewire","USB",
    "Display","iPad","iPod","MacBook","iMac","PowerMac",];

//ticket model
var Ticket = Backbone.Model.extend({
    urlRoot: "/ticket",
    initialize: function(){
        var self = this;
        self.notes = new Notes({ticketId: self.get("id")});
        self.notes.fetch();
        
    },
    elevate: function(elevationMeta){
        var self = this;
        self.save({
            elevated: true,
            elevated_reason: elevationMeta,
        });
        self.fetch({wait: true});
    },
    deelevate: function(){
        var self = this;
        self.save({
            elevated: false,
        });
        self.fetch({wait: true});
    },
    close: function(completedMeta){
        var self = this;
        self.save({
            closed: true,
            completed_meta: completedMeta,
        });
        self.fetch({wait: true});
    },
    reopen: function(){
        var self = this;
        self.save({
            closed: false,
        });
        self.fetch({wait: true});
    },
    toggleStar: function(){
        var self = this;
        self.save({
            starred: !self.get("starred"),
        });
    },
    reassign: function(assignTo){
        var self = this;
        self.save({
            assigned_to: assignTo,
        });
        self.fetch({wait: true});
    },
    inventory: function(changeTo){
        var self = this;
        self.save({
            inventory: changeTo,
        });
        self.fetch({wait: true});
    },
    prioritize: function(){
        var self = this;
        self.save({
            priority: !self.get("priority"),
        });
        console.log(self);
    },
});

//note model
var Note = Backbone.Model.extend({
    urlRoot: function(){
        var self = this;
        if (self.get("id")){
            return '/note';
        } else {
            return '/note/'+'new';
        }
    },
});

//notes collection
var Notes = Backbone.Collection.extend({
    model: Note,
    url: function(){
        var self = this;
        return '/notes/'+self.ticketId;
    },
    initialize: function(options){
        var self = this;
        self.ticketId = options.ticketId;
    },
    removeNote: function(id){
        var self = this;
        self.get(id).destroy({
            wait: true,
        });
    },
    addNote: function(note){
        var self = this;
        if (note !== ''){
            if (note.indexOf(':') == -1){
                var newNote = new Note({
                    for_ticket: self.ticketId,
                    message: note,
                });
            } else {
                var assignedTo = note.slice(0, note.indexOf(':')); 
                var thisMessage = note.slice(note.indexOf(':')+1, note.length);
                var newNote = new Note({
                    for_ticket: self.ticketId,
                    message: thisMessage,
                    assigned_to: assignedTo,
                });
            }
            console.log(newNote);
            newNote.save();
            self.fetch({wait: true});
        }
    },
});

//tickets collection
var Tickets = Backbone.Collection.extend({
    model: Ticket,
    url: '/tickets',
    initialize: function(){
        var self = this;
    },
    closed: function(){
        var self = this;
        var theseTickets = self.filter(function(ticket){
            return ticket.get("closed");
        });
        return theseTickets.length;
    },
    open: function(){
        var self = this;
        var theseTickets = self.filter(function(ticket){
            return !ticket.get("closed");
        });
        return theseTickets.length;
    },
    elevated: function(){
        var self = this;
        var theseTickets = self.filter(function(ticket){
            return ticket.get("elevated");
        });
        return theseTickets.length;
    },
    comparator:function(ticket){
        return [!ticket.get("priority"), !ticket.get("starred"), !ticket.get("closed")]
    },
    parse: function(response){
        for (var i=0;i<=response.length-1;i++){
            if (!response[i].closed){
                response[i].completed_on = false;
                response[i].completed_by = false;
            } else {
                var fixedDate = new Date(response[i].completed_on.replace(/-/g,'/').replace(/T/,' ').replace(/\+/,' +')).toString();
                response[i].completed_on = fixedDate.slice(0, fixedDate.indexOf('GMT')-4);
            }
            if (!response[i].elevated){
                response[i].elevated_on = false;
                response[i].elevated_by = false;
            } else {
                var fixedDate = new Date(response[i].elevated_on.replace(/-/g,'/').replace(/T/,' ').replace(/\+/,' +')).toString();
                response[i].elevated_on = fixedDate.slice(0, fixedDate.indexOf('GMT')-4);
            }
            var fixedDate = new Date(response[i].submitted_on.replace(/-/g,'/').replace(/T/,' ').replace(/\+/,' +')).toString();
            response[i].submitted_on = fixedDate.slice(0, fixedDate.indexOf('GMT')-4);
            response[i].submitted_by = response[i].submitted_by.slice(0, response[i].submitted_by.indexOf('@'));
        }
        return response;
    },
});

//single ticket view in window
var SingleTicket = Backbone.View.extend({
    events: {
        "dblclick #addNote": "getNote",
        "keypress #newNote": "addNote",
        "keypress #newAssignment": "setReassignment",
        "keypress #newInventory": "setInventory",
        "dblclick .removeMe": "removeNote",
        "dblclick #reassign": "getReassignment",
        "dblclick #inventory": "getInventory",
        "click #closeMe": "closeTicket",
        "click #elevateMe": "elevateTicket",
        "click #reopen": "reopenTicket",
        "click #deelevate": "deelevateTicket",
        "click .cancel": "render",
        "click .sortme": "sortMe",
        "click #prioritize": "prioritize",
    },
    initialize: function(){
        var self = this;
        self.model.bind('all', self.render, self);
        self.model.notes.bind('all', self.render, self);
    },
    render: function(){
        var self = this;
        var thisTicket = self.model.attributes;
        var theseNotes = [];
        for (var i=0;i<=self.model.notes.length-1;i++){
            theseNotes.push(self.model.notes.models[i].attributes);
        }
        var source = $('#singleTicketTemplate').html();
        var template = Handlebars.compile(source);
        var options = {
            elevatedButton: function(thisTicket){
                if(thisTicket.elevated){
                    return ' disabled';
                } else {
                    return '';
                }
            },
            elevatedText: function(thisTicket){
                if(thisTicket.elevated){
                    return 'Elevated';
                } else {
                    return 'Elevate';
                }
            },
            elevatedMeta: META_LIST,
            completeMeta: COMPLETE_META,
        }

        var context = {
            ticket: thisTicket,
            notes: theseNotes,
            options: options,
        }
        var source = template(context);
        $(self.el).html(source);
        $('.chzn-select').chosen({allow_single_deselect:true});
        $('.noteInformation').each(function(){
            $(this).tooltip({
                animation: false,
            });
        });
        return self;
    },
    prioritize: function(){
        var self = this;
        self.model.prioritize();
    },
    sortMe: function(e){
        console.log($(e));
    },
    closeTicket: function(){
        var self = this;
        var completedMeta = $('#completedMeta').val();
        self.model.close(completedMeta);
    },
    reopenTicket: function(){
        var self = this;
        self.model.reopen();
    },
    elevateTicket: function(){
        var self = this;
        var elevationMeta = $('#elevationMeta').val();
        self.model.elevate(elevationMeta);
    },
    deelevateTicket: function(){
        var self = this;
        self.model.deelevate();
    },
    getInventory: function(){
        var self = this;
        $('#inventory').html('<strong>Reassign inventory number:</strong><div class="input-append"><input id="newInventory" type="text" class="input span2"><button class="btn cancel"><i class="icon-remove"></i></button></div>');
        $('#newInventory').focus();
    },
    setInventory: function(e){
        var self = this;
        var newNumber = $('#newInventory').val();
        if (e.keyCode === 27){
            self.render();
            return;
        }
        if (!newNumber || e.keyCode !== 13){
            return;
        }
        self.model.inventory(newNumber);
    },
    getReassignment: function(){
        var self = this;
        $('#reassign').html('<strong>Reassign to email:</strong><div class="input-append"><input id="newAssignment" type="text" class="input span2"><button class="btn cancel"><i class="icon-remove"></i></button></div>');
        $('#newAssignment').focus();
    },
    setReassignment: function(e){
        var self = this;
        var reassignment = $('#newAssignment').val();
        if (e.keyCode === 27){
            self.render();
            return;
        }
        if (!reassignment || e.keyCode !== 13){
            return;
        }
        self.model.reassign(reassignment);
    },
    getNote: function(){
        var self = this;
        $('#addNote', self.el).remove();
        $('#ticketNotes', self.el).append('<li id="newNoteList"><div class="input-append"><input id="newNote" type="text" class="input span2"><button class="btn cancel"><i class="icon-remove"></i></button></div></li>');
        $('#newNote').focus();
    },
    addNote: function(e){
        var self = this;
        var note = $('#newNote', self.el).val();
        if (e.keyCode === 27){
            self.render();
            return;
        }
        if (!note || e.keyCode !== 13){
            return;
        }
        self.model.notes.addNote(note);
    },
    removeNote: function(e){
        var self = this;
        var thisNote = $(e.srcElement).attr('note-id');
        self.model.notes.removeNote(thisNote);
    },
});

//ticket view in the list
var TicketView = Backbone.View.extend({
    tagName: "li",
    className: "ticketListItem",
    events: {
        "click": "expandTicket",
        "click .favMe": "toggleStar",
    },
    initialize: function(){
        var self = this;
        self.model.bind('change', self.render, self);
    },
    render: function(){
        var self = this;
        var starred = 'icon-star-empty';
        var thisTicket = self.model.attributes;
        if (thisTicket.starred){
            starred = 'icon-star';
        }
        var source = $('#ticketListTemplate').html();
        var template = Handlebars.compile(source);
        var context = {
            ticket: thisTicket,
            icon: starred,
        }
        var source = template(context);
        $(self.el).html(source);
        $('.chzn-select').chosen({allow_single_deselect:true});
        return self;
    },
    toggleStar: function(){
        var self = this;
        self.model.toggleStar();
    },
    expandTicket: function(){
        var self = this;
        $('.ticketListItem').each(function(){
            $(this).removeClass('active');
        });
        $(self.el).addClass('active');
        var thisTicket = new SingleTicket({
            model: this.model,
        });
        $('#layoutSingleTicket').html(thisTicket.render().el);
        $('.chzn-select').chosen({allow_single_deselect:true});
        $('.noteInformation').each(function(){
            $(this).tooltip({
                animation: false,
            });
        });
    },
});

//base application view
var HelpDesk = Backbone.View.extend({
    tickets: new Tickets(),
    events: {
        "change #displayOptions": "setFilter",
        "keypress #displaySearch": "setSearch",
    },
    initialize: function(options){
        var self = this;

        self.userName = options.parameters.user_name;
        self.displayOptions = 'Open';
        self.displaySearch = '';
        
        self.tickets.bind('all', self.render, self);
        self.tickets.fetch();

        self.render();
    },
    render: function(){
        var self = this;
        self.addAll();
        var source = $('#appHeaderTemplate').html();
        var template = Handlebars.compile(source);
        var context = {
            options: {
                username: self.userName,
                openTickets: self.tickets.open(),
                closedTickets: self.tickets.closed(),
                oldestTicket: "oldestTicket",
                averageAge: "averageAge",
            },
        };

        var source = template(context);
        $(self.el).html(source);
        $('#displayOptions').val(self.displayOptions);
        $('#displaySearch').val(self.displaySearch);
        return self;
    },
    sortMe: function(e){
        console.log($(e.srcElement).val());
    },
    setSearch: function(e){
        var self = this;
        if (e.keyCode !== 13){
            return;
        };
        self.displaySearch = $('#displaySearch').val();
        self.addAll();
    },
    setFilter: function(){
        var self = this;
        self.displayOptions = $('#displayOptions').val();
        self.addAll();
    },
    addOne: function(ticket){
        var self = this;
        var view = new TicketView({
            model: ticket,
        });
        $('#layoutTicketList ul', self.el).append(view.render().el);
    },
    addAll: function(){
        var self = this;
        var theseTickets;
        $('.ticketListItem').each(function(){
            $(this).remove();
        });
        if (self.displayOptions == 'Open'){
            theseTickets = self.tickets.filter(function(ticket){
                return !ticket.get("closed");
            });
        } else if (self.displayOptions == 'Closed'){
            theseTickets = self.tickets.filter(function(ticket){
                return ticket.get("closed");
            });
        } else if (self.displayOptions == 'All'){
            theseTickets = self.tickets.filter(function(ticket){
                return ticket;
            });
        }

        if (self.displaySearch !== ''){
            if (self.displaySearch.indexOf(',') == -1){
                var searchTerms = [];
                searchTerms.push(self.displaySearch);
            } else {
                var searchTerms = self.displaySearch.split(',');
            }
            for (var i=0;i<=searchTerms.length-1;i++){
                if (searchTerms[i].indexOf(':') == -1){
                    theseTickets = theseTickets.filter(function(ticket){
                        if (ticket.get("description").match('.*'+searchTerms[i]+'.*')){
                            return ticket;
                        }
                    });
                } else {
                    var separaterIndex = searchTerms[i].indexOf(':');
                    var parameter = searchTerms[i].slice(0, separaterIndex);
                    var argument = searchTerms[i].slice(separaterIndex+1, searchTerms[i].length);
                    switch(parameter){
                        case 'id':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ticket.get("id") == argument;
                            });
                            break;
                        case 'who':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ticket.get("submitted_by") == argument;
                            });
                            break;
                        case 'what':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ticket.get("type") == argument;
                            });
                            break;
                        case 'where':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ((ticket.get("macro") == argument) ||
                                    (ticket.get("micro") == argument));
                            });
                            break;
                        case 'user':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ticket.get("user_type") == argument;
                            });
                            break;
                        case 'starred':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ticket.get("starred");
                            });
                            break;
                        case 'elevated':
                            theseTickets = theseTickets.filter(function(ticket){
                                return ticket.get("elevated");
                            });
                            break;
                        case 'meta':
                            theseTickets = theseTickets.filter(function(ticket){
                                if (ticket.get("elevated") && ticket.get("elevated_reason").toLowerCase().match('.*'+argument.toLowerCase()+'.*')){
                                    return ticket;
                                }
                            });
                            break;
                    }
                }
            }
        }
        theseTickets = _.sortBy(theseTickets, function(ticket){
            return [!ticket.get("priority"), !ticket.get("starred"), ticket.get("closed")]
        });
        theseTickets.forEach(self.addOne);
    },
});

var Shortcuts = Backbone.Router.extend({
    initialize: function(options){
        var self = this;
        self.user_name = options.user_name;
        self.token = options.token;
    },
    routes: {
        "ticket/:id": "singleTicket",
        "*actions": "defaultRoute",
    },
    singleTicket: function(id){
        var self = this;
        if (!self.manageTickets){
            self.defaultRoute();
        }
        $('#displaySearch').val('id:'+id);
        var e = jQuery.Event("keypress");
        e.keyCode = 13;
        $('#displaySearch').trigger(e);
    },
    defaultRoute: function(actions){
        var self = this;
        self.manageTickets = new HelpDesk({
            el: $('#layoutAppHeader'),
            parameters: { user_name: self.user_name },
        });
        channel = new goog.appengine.Channel(self.token);
        socket = channel.open();
        socket.onmessage = self.manageTickets.tickets.fetch;
    },
});
