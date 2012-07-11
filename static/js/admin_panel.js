function Checked(e){
    if (e.attr('checked')){
        return true;
    } else {
        return false;
    }
}

function ParseSites(user){
    var theseSites = [];
    for (var i=0;i<=SITES.length-1;i++){
        var match = false;
        for (var j=0;j<=user.get('sites').length-1;j++){
            if (user.get('sites')[j] == SITES[i]){
                match = true;
            }
        }
        if (match){
            theseSites.push({
                name: SITES[i],
                selected: true,
            });
        } else {
            theseSites.push({
                name: SITES[i],
                selected: false,
            });
        }
    }
    return theseSites;
}

var SITES = [
    'DIST',
    'WHS',
    'EHS',
    'MHS',
    'OVHS',
    'HBHS',
    'FVHS',
    'CHS',
    'CDS',
    'HBAS',
    'VVHS',
    'Food Services',
    'Transportation',
    ]

// single user model
var User = Backbone.Model.extend({
    urlRoot: function(){
        var self = this;
        if (self.get("id")){
            return '/user';
        } else {
            return '/user/'+'new';
        }
    },
    initialize: function(){
    },
    parse: function(response){
        if (response.last_login){
            var fixedDate = new Date(response.last_login.replace(/-/g,'/').replace(/T/,' ').replace(/\+/,' +')).toString();
            response.last_login = fixedDate.slice(0, fixedDate.indexOf('GMT')-4);
        }
        return response;
    },
});

// users collection
var Users = Backbone.Collection.extend({
    model: User,
    url: "/users",
    initialize: function(){
    },
    
});

// main app view
var AdminPanel = Backbone.View.extend({
    users: new Users(),
    events: {
        "click #cancelNewUser": "render",
        "click #cancelEditUser": "render",
        "dblclick #addUser": "getUser",
        "dblclick .user": "editUser",
        "keypress #newUser": "addUser",
        "keypress #editUser": "makeEdit",
        "click #confirmNewUser": "addUser",
        "click #confirmEditUser": "makeEdit",
        "click #deleteUser": "deleteUser",
    },
    initialize: function(){
        var self = this;
        
        self.users.bind('all', self.render, self);
        self.users.fetch();
        self.render();
    },
    render: function(){
        var self = this;
        var source = $('#userListTemplate').html();
        var template = Handlebars.compile(source);
        var context = {
            users: self.users.models,
        };
        var source = template(context);
        $(self.el).html(source);
        return self;
    },
    deleteUser: function(){
        var self = this;
        self.users.get($('#editUser').attr('user-id')).destroy({wait: true});
    },
    editUser: function(e){
        var self = this;
        $('.user').each(function(){
            $(this).removeClass('user');
        });
        var thisUser = self.users.get($(e.currentTarget).attr('user-id'));
        var source = $('#editUserTemplate').html();
        var template = Handlebars.compile(source);
        var context = {
            user: thisUser,
            sites: ParseSites(thisUser),
        }
        var source = template(context);
        $(e.currentTarget).html(source);
        $(e.currentTarget).attr('id', 'editUser');
        $('.chzn-select').chosen({allow_single_deselect:true});
        $('#firstname').focus();
    },
    makeEdit: function(e){
        var self = this;
        var firstname = $('#firstname', self.el).val();
        var lastname = $('#lastname', self.el).val();
        var email = $('#email', self.el).val();
        var sites = $('#sites', self.el).val();
        var nettech = Checked($('#nettech', self.el));
        var admin = Checked($('#admin', self.el));
        var ets = Checked($('#ets', self.el));
        var informationSet = (firstname !== '' && lastname !== '' && sites !== '' && email.indexOf('@') !== -1);
        var permissionsSet = (admin || ets || nettech);
        if (e.keyCode === 27){
            self.render();
            return;
        }
        if (e.type !== "click" &&(!informationSet || !permissionsSet || e.keyCode !== 13)){
            return;
        }
        var editUser = self.users.get($('#editUser').attr('user-id'));
        editUser.save({
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'nettech': nettech,
            'admin': admin,
            'ets': ets,
            'sites': sites,
        });
        self.users.fetch();
        self.render();
    },
    getUser: function(){
        var self = this;
        $('#addUser', self.el).remove();
        var source = $('#newUserTemplate').html();
        var template = Handlebars.compile(source);
        var context = {
            sites: SITES,
        }
        var source = template(context);
        $('#userList', self.el).append(source);
        $('.chzn-select').chosen({allow_single_deselect:true});
        $('#firstname').focus();
    },
    addUser: function(e){
        var self = this;
        var firstname = $('#firstname', self.el).val();
        var lastname = $('#lastname', self.el).val();
        var email = $('#email', self.el).val();
        var sites = $('#sites', self.el).val();
        var nettech = Checked($('#nettech', self.el));
        var admin = Checked($('#admin', self.el));
        var ets = Checked($('#ets', self.el));
        var informationSet = (firstname !== '' && lastname !== '' && sites !== '' && email.indexOf('@') !== -1);
        var permissionsSet = (admin || ets || nettech);
        if (e.keyCode === 27){
            self.render();
            return;
        }
        if (e.type !== "click" &&(!informationSet || !permissionsSet || e.keyCode !== 13)){
            return;
        }
        var newUser = new User({
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'nettech': nettech,
            'admin': admin,
            'ets': ets,
            'sites': sites,
        });
        newUser.save({wait: true});
        self.users.fetch();
        self.render();
    },
});
