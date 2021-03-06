from flask import Flask, request, redirect, url_for, render_template, flash, session
from werkzeug import secure_filename
from pymongo import Connection
from pytesseract import *
from PIL import Image
import json, urllib2
import os
import base64
import cgi
import cgitb; cgitb.enable()

UPLOAD_FOLDER = './static/'
ALLOWED_EXTENSIONS = set(['png', 'bmp', 'jpg'])

form = cgi.FieldStorage()

app = Flask(__name__, static_url_path="/static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret"
conn = Connection()
db = conn ['stuyapp']

def checkFormat(L): #checks the format of user's schedule- class/section/teacher vs pd/class/title
    print L
    L = ''.join(L.split())
    L = L.lower()
    if L == "classsectionteacher":
        return "class"
    if L[:5] == "class":
        return "class"
    if L[:-8] == "teacher":
        return "class"
    if L == "pdcodetitle":
        return "pd"
    if L[:2] == "pd":
        return "pd"
    if L[:-5] == "title":
        return "pd"
    return "fail"

def join(L): #Joins a list of strings by spaces
    s = ""
    for i in L:
        s = s + i + " "
    return s[:-1]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/")
def home(): 
    if 'user' in session:
        q = db.users.find_one({'name':session['user']})
        #print "in session"
        msgs = q['messages']
        #print msgs
        user = ", " + session['user']
        url1="schedule"
        link1="Schedule"
        url2="logout"
        link2="Logout"
    else:
        msgs=[]
        user = ""
        url1="login"
        link1="Login"
        url2="register"
        link2="Register"
    return render_template("home.html", user=user, msgs=msgs, url1=url1, url2=url2, link1=link1, link2=link2)

@app.route("/test")
def test():
    #return '''<html>
    '''<body>
<script>
  window.fbAsyncInit = function() {
    FB.init({
      appId      : '840810872652744',
      xfbml      : true,
      version    : 'v2.2'
    });
  };

  (function(d, s, id){
     var js, fjs = d.getElementsByTagName(s)[0];
     if (d.getElementById(id)) {return;}
     js = d.createElement(s); js.id = id;
     js.src = "//connect.facebook.net/en_US/sdk.js";
     fjs.parentNode.insertBefore(js, fjs);
   }(document, 'script', 'facebook-jssdk'));
</script>
<div
  class="fb-like"
  data-share="true"
  data-width="450"
  data-show-faces="true">
</div>
</body>
</html>'''
    return '''<!DOCTYPE html>
<html>
<head>
<title>Facebook Login JavaScript Example</title>
<meta charset="UTF-8">
</head>
<body>
<script>
  // This is called with the results from from FB.getLoginStatus().
  function statusChangeCallback(response) {
    console.log('statusChangeCallback');
    console.log(response);
    // The response object is returned with a status field that lets the
    // app know the current login status of the person.
    // Full docs on the response object can be found in the documentation
    // for FB.getLoginStatus().
    if (response.status === 'connected') {
      // Logged into your app and Facebook.
      testAPI();
    } else if (response.status === 'not_authorized') {
      // The person is logged into Facebook, but not your app.
      document.getElementById('status').innerHTML = 'Please log ' +
        'into this app.';
    } else {
      // The person is not logged into Facebook, so we're not sure if
      // they are logged into this app or not.
      document.getElementById('status').innerHTML = 'Please log ' +
        'into Facebook.';
    }
  }

  // This function is called when someone finishes with the Login
  // Button.  See the onlogin handler attached to it in the sample
  // code below.
  function checkLoginState() {
    FB.getLoginStatus(function(response) {
      statusChangeCallback(response);
    });
  }

  window.fbAsyncInit = function() {
  FB.init({
    appId      : '840810872652744',
    cookie     : true,  // enable cookies to allow the server to access 
                        // the session
    xfbml      : true,  // parse social plugins on this page
    version    : 'v2.1' // use version 2.1
  });

  // Now that we've initialized the JavaScript SDK, we call 
  // FB.getLoginStatus().  This function gets the state of the
  // person visiting this page and can return one of three states to
  // the callback you provide.  They can be:
  //
  // 1. Logged into your app ('connected')
  // 2. Logged into Facebook, but not your app ('not_authorized')
  // 3. Not logged into Facebook and can't tell if they are logged into
  //    your app or not.
  //
  // These three cases are handled in the callback function.

  FB.getLoginStatus(function(response) {
    statusChangeCallback(response);
  });

  };

  // Load the SDK asynchronously
  (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'facebook-jssdk'));

  // Here we run a very simple test of the Graph API after login is
  // successful.  See statusChangeCallback() for when this call is made.
  function testAPI() {
    console.log('Welcome!  Fetching your information.... ');
    FB.api('/me', function(response) {
      console.log('Successful login for: ' + response.name);
      document.getElementById('status').innerHTML =
        'Thanks for logging in, ' + response.name + '!';
    });
  }
</script>

<!--
  Below we include the Login Button social plugin. This button uses
  the JavaScript SDK to present a graphical Login button that triggers
  the FB.login() function when clicked.
-->

<fb:login-button scope="public_profile,email" onlogin="checkLoginState();">
</fb:login-button>

<div id="status">
</div>

</body>
</html>'''

@app.route("/search", methods=["GET", "POST"])
def search():
    select = request.args.get("select")
    search = request.args.get("search")
    return redirect("/"+select+"/"+search)

@app.route("/about")
def about():
    return render_template("about.html", logged = 'user' in session)

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    for x in db.classes.find():
        #print x
        c = x['code']
        for y in db.classes.find({'code':c}):
            print "same code: " + str(y)
        #print '\n'
    #print "method schedule"
    username = session['user']
    #print "user in session"
    if request.method == "POST":
        newSched = request.form.get("new", None)
        otherSched = request.form.get("other", None)
        req = request.form.get("request", None)
        if newSched != None:
            #print "schedule method = post"
            #print str(db.users.find_one({'name':username}))
            q = db.classes.find()
            print q
            for classs in q:
                print "class: " + str(classs)
                code = classs['code']
                #print classs['sections']
                #for section in classs:
                print "sections: " + str(classs['sections'])
                sections = classs['sections']
                for section in sections:
                    print "section: " + section
                    students = sections[section]
                    print "students in section: " + str(students)
                    print "username: " + username
                    if username in students:
                        students.remove(username)
                    sections[section]=students
                    print "removed "
                #print "class[section]: " + str(classs[section])
                #remove name from classes
                db.classes.update({'code':code}, {'$set':{'sections':sections}})
            db.users.update({"name":username},{'$set':{'confirmed':0}})
            return redirect(url_for("loggedin"))
        elif otherSched != None:
            db.users.update({"name":username},{'$set':{'confirmed':0}})
            #print str(db.users.find_one({'name':username}))
            return redirect(url_for("loggedin"))
        elif req != None:
            return render_template("request.html")
        else:
            return "error, shouldn't happen"
    '''elif request.method=="GET" and request.args.get("q", None)!=None:
        t = request.args.get("r", None)
        query = request.args.get("q", None)
        if t == None or query == "":
            return "please fill out all fields"
        return "search"'''
    print "schedule"
    x = db.users.find_one({'name':username})

    #for i in db.classes.find():
    #print i
    #print "schedule2"

    periods = {}
    teachers = {}

    #print "checkerror"

    #print "checkerror2"
    q = db.users.find_one({'name':username})
    #print str(q)
    schedule = q['schedule']
    titles = []
    periods = []
    sections = []
    teachers = []
    #print range(len(schedule))
    print str(schedule)
    for i in range(len(schedule)):
        #print 'i in schedule: ' + str(i)
        qu = db.classes.find_one({'code':schedule[i]})
        #print "code: " + schedule[i]
        #print "q: " + str(qu)
        if 'title' in qu:
            title = qu['title']
            #print 'title in qu: ' + title
            titles.append(title)
        else:
            #print "title not appended"
            titles.append("")
        '''if 'teacher' in qu:
            teacher = qu['teacher']
            print 'teacher in q: ' + teacher
            teachers.append(teacher)'''
        #print 'title/teacher done'
        que = qu['sections']
        for pdorsection in que:
            #print "period or section: " + pdorsection
            if pdorsection[:2]=="pd":
                period = que[pdorsection]
                #print "people in pd: " + str(period)
                if username in period:
                    periods.append(pdorsection[2:])
            else:
                section = que[pdorsection]
                teacher = pdorsection[pdorsection.find(",")+2:]
                #print "adding teacher:" + teacher
                #print "people in section: " + str(section)
                if username in section:
                    #print "usr in period"
                    teachers.append(teacher)
                    sections.append(pdorsection[:pdorsection.find(",")])
    #print str(q)
    #print "codes: " + str(schedule)
    #print "teachers: " + str(teachers)
    #print "titles: " + str(titles)
    #print "sections: " + str(sections)
    #print "periods: " + str(periods)
    #for x in db.classes.find():
    #print "class: " + str(x)
    #print str(db.users.find_one({'name':username}))
    if len(sections)>0 and len(periods)>0:
        print "match sections and periods here"
        print "sections: " + str(sections)
        print "periods: " + str(periods)
        if len(sections)==len(periods):
            for i in range(len(schedule)):
                db.classes.update({'code':schedule[i]}, {'$set': {sections[i]+", " + teachers[i]:periods[i], periods[i]:sections[i]+", "+teachers[i]}})
                print "matches in document: " + str(db.classes.find_one({'code':schedule[i]}))
                print "code: " + schedule[i]
                print "section: " + sections[i]
                print "period: " + periods[i]
    else:
        if len(periods)>0:
            print "periods"
            for i in range(len(periods)):
                code = schedule[i]
                period = periods[i]
                print "code: " + code
                print "period: " + period
                q = db.classes.find_one({'code':code})
                print "q: " + str(q)
                if period in q:
                    print "period is in code: " + period
                    section = q[period]
                    print "section: " + str(section)
        elif len(sections)>0:
            print "sections"
            for i in range(len(sections)):
                print "i: " + str(i)
                code = schedule[i]
                section = sections[i]
                #print "code: " + code
                #print "section: " + section
                q = db.classes.find_one({'code':code})
                print "q: " + str(q)
                if section in code:
                    print "section is in code"
                    period = q[section]
                    print "period: " + period
    if len(periods)>0:
        newPeriods = []
        for x in periods:
            newPeriods.append(int(x))
        #newPeriods.sort()#[0,0,0,0,0,0,0,0,0,0]
        periodsDict={}
        for x in periods:
            periodsDict[periods.index(x)]=newPeriods.index(int(x))
        print "pddict: " + str(periodsDict)
        print "periods: " + str(periods)
        print "teachers: " + str(teachers)
        print "codes: " + str(schedule)
        newTeachers = ['', '', '', '', '', '', '', '', '', '']
        newSchedule = ['', '', '', '', '', '', '', '', '', '']
        newSections = ['', '', '', '', '', '', '', '', '', '']
        newTitles = ['', '', '', '', '', '', '', '', '', '']
        for x in periodsDict:
            #print "pddict for loop: " + str(x)
            y = periodsDict[x]
            print str(x) + " becomes " + str(y)
            #print y
            newSchedule.pop(y)
            newSchedule.insert(y, schedule[x])
            #code = schedule[y]
            print "code: " + newSchedule[y]
            print "codes: " + str(newSchedule)
            newTeachers.pop(y)
            newTeachers.insert(y, teachers[x])
            #teacher = teachers[y]
            print "teacher: " + newTeachers[y]
            print "teachers: " + str(newTeachers)
            newTitles.pop(y)
            newTitles.insert(y, titles[x])
            #title = titles[y]
            print "title: " + newTitles[y]
            #newsection = sections.pop(x)
            newSections.pop(y)
            newSections.insert(y, sections[x])
            #section = sections[y]
            print "section: " + newSections[y]
        print "newPeriods: " + str(newPeriods)
        newPeriods.sort()
        periods = newPeriods
        print "newSections: " + str(newSections)
        sections = newSections
        print "newTitles: " + str(newTitles)
        titles = newTitles
        print "newTeachers: " + str(newTeachers)
        teachers = newTeachers
        print "newCodes: " + str(newSchedule)
        schedule = newSchedule
        #for i in range(len(periods)):
        #print "for loop: " + str(i)
        #print "period: " + periods[i]
        #    newPeriods.insert(int(periods[i]),periods[i])
        print "newPeriods: " + str(newPeriods)
        #print "periods in schedule" + str(periods)
        i = 1
        #frees = []
        while i <= 10:
            #print "while i " + str(i)
            if i not in periods:
                #print "i not there " + str(i)
                #frees.append(i)
                if schedule[i][0].upper()=="Z":
                    print "LUNCH"
                else:
                    print "not lunch: " + schedule[i]
                    print "index: " + str(i)
                schedule.insert(i-1, "None")
                titles.insert(i-1, "Free")
                periods.insert(i-1, i)
                q = db.classes.find_one({'code':'FREE'})
                #print "q free: " + str(q)
                if q == None:
                    #print "none"
                    db.classes.insert({'code':'FREE', 'sections':{}})
                db.classes.remove({'code':'FREE'})
                db.classes.insert({'code':'FREE', 'sections':{}})
                #print "ok till now"
                q = db.classes.find_one({'code':'FREE'})
                #print "q free: " + str(q)
                fsections = q['sections']
                #print "sections: " + str(fsections)
                if str(i) not in fsections:
                    #print str(i) + " isnt in q"
                    #print "usr: " + str(fsections[str(i)])
                    fsections[str(i)]=[username]
                    #print "ok"
                    #print "usr: " + username
                    db.classes.update({'code':'FREE'}, {'$set': {'sections': fsections}})
                    #print "free document: " + str(db.classes.find_one({'code':'FREE'}))
                else:
                    fsections = q['sections']
                    students = fsections[str(i)]
                    students.append(username)
                    fsections[str(i)]=students
                    db.classes.update({'code':'FREE'} , {'$set': { 'sections': fsections }})
                #print "q: " + str(q)
                #else:
                #students = q[str(i))
                #db.classes.update({'code':'free'}, {'$set': 
            i = i + 1
    i = len(sections)-1
    while i >= 0:
        #for i in range(len(sections)):
        #print i
        #print sections[i]
        item = sections.pop(i)[-2:]
        sections.insert(i, item)
        #print sections[i]
        #schedule[i] = schedule.pop(i)[:-2]'''
        i = i - 1
    return render_template("schedule2.html", L = schedule, D = schedule, T = teachers, titles=titles, T2=teachers, periods=periods, teachers=teachers, sections=sections, col1="Code", col2="Class", col3="Teacher", col4="Section", col5="Period", schedule=schedule)

@app.route("/class/<code>", methods=["GET", "POST"])
def classpage(code):
    code = code.upper()
    print code
    if request.method=="POST":
        username = session['user']
        thisSection = request.form.get("requested", None).replace("-", ",")
        code = request.form.get("code", None)
        #print "classcode: " + code + "endcode"
        #print "class thissection:P " + thisSection
        #print "end section"
        q = db.classes.find_one({'code':code})
        if 'title' in q:
            title = q['title']
        else:
            title = ''
        #print "title" + title
        #print "q: "
        #print str(q)
        #print "AAAH"
        qSections = q['sections']
        #print "qsections: "
        #print str(qSections).replace("\r","")
        #for s in qSections:
        #print "s:"
        #print s
        #print "thisSection: " + thisSection+"endsection"        
        #users = qSections[thisSection]
        #print "hello"
        #print thisSection.replace("\n", "")
        if thisSection.replace("\n","") in qSections:
            #print "users: "
            users = qSections[thisSection.replace("\n","")]
            #print "done"
            if title=='':
                s = username + " would like your spot in " + thisSection + " in " + code
            else:
                s = username + " would like your spot in " + thisSection + " of " + title + " class"
            #print s
            req(users, s)
            flash("Request Submitted!")
        #else:
        #print "fail"
        '''for doc in db.classes.find():
            print doc
            sections = doc['sections']
            print "class sections: " + str(sections)
            for section in sections:
                print section
                if section.replace==thisSection:
                    print "correct doc? " + str(sections[section])
                    users = sections[section]
                    print "users; " + str(users)
                    s = username + " would like your spot in " + thisSection + " of " + thisTeacher + "'s class"
                    print s
                    req(users, s)
                    flash("Request Submitted!")
                else:
                    print "incorrect doc? " + str(section).replace("\r","\n")+"enddoc"
                    print "thissection" + thisSection + "endsection"'''
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    code = code.replace("%20"," ")
    q = db.classes.find_one({'code':code})
    print "q in search class: " + str(q)
    if q == None:
        q = db.classes.find_one({'title':code})
        if q == None:
            if code == "NONE":
                return redirect("/class/free")
            #return "Your search yielded no results"
            flash ("Your search yielded no results")
            return redirect("/")
        code = q['code']
        return redirect("/class/"+code)
    else:
        if 'title' in q:
            title = q['title']
        else:
            title = "N/A"
    #y = db.classes.find({'code':code[:-2]})
    #for x in db.classes.find():
    #print "x"
    #print x['code']
    #print "code: " + code
    #print "q: " + str(q)
    classList = q['sections']
    #print "classList: " + str(classList)
    studentsInClass = {}
    for x in classList:
        print "element in classlist: " + x
        print "class[x]" + str(classList[x])
        studentsInClass[x]=classList[x]
        print studentsInClass
        if x[:2]!="pd" and code!="FREE":
            teacher = x[x.find(",")+2]
        else:
            teacher = "N/A"
    #if (x == None):
    #return "This class does not exist"
    
    similar = []
    #for i in y:
    #similar.append(i['ext'])
    #students = x['students']
    #if 'period' in x:
    #    period = x['period']
    #else:
    #    period = "Unknown"
    #teacher = x['teacher']
    print "return here"
    return render_template("class.html", code=code, similar = [], students = studentsInClass, teacher = teacher, title=title)

def req(users, s):
    #print "request submit"
    username = session['user']
    for user in users:
        if username != user:
            #print 'user: ' + user
            q = db.users.find_one({'name':user})
            #if q == None:
            #print "none"
            #print "q: " + str(q)
            messages = q['messages']
            #print "msgs: " + str(messages)
            messages.append(s)
            db.users.update({'name':user}, {'$set':{'messages':messages}}, multi=True)
        print str(db.users.find_one({'name':user}))

@app.route("/teacher/<teacher>", methods=["GET", "POST"])
def teacherpage(teacher):
    username = session['user']
    #print "teacher"
    thisTeacher = teacher.replace("%20"," ").upper()
    #print "thisTeacher: " + thisTeacher
    if request.method=="POST":
        #print "get"
        thisSection = request.form.get("requested", None)
        for doc in db.classes.find():
            sections = doc['sections']
            for section in sections:
                if "," in section:
                    teacher = section[section.find(',')+2:]
                    #print "\n"
                    #print teacher.lower() == thisTeacher+"\r"
                    #print section[:section.find(',')]==thisSection+"\r"
                    if teacher.upper() == thisTeacher and section[:section.find(',')]==thisSection:
                        #print "correct doc? " + str(sections[section])
                        users = sections[section]
                        #print "users; " + str(users)
                        s = username + " would like your spot in " + thisSection + " of " + thisTeacher + "'s class"
                        #print s
                        req(users, s)
                        flash("Request Submitted!")
                    #else:
                        #print "thisteacher: " + thisTeacher
                        #print "teacher: " + teacher.lower()
                        #print "section: " + section[:section.find(',')]
                        #print "thisSection: " + thisSection
        #print doc
        #print "post"
        #print "section: " + str(section)
        #users = db.classes.find_one('')
        #users = users.split()
        #print "users after: " + str(users)
        #for user in users:
        #print "user: " + str(user)
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    teachersClasses = {}
    codes = []
    for doc in db.classes.find():
        sections = doc['sections']
        #print "sections: " + str(sections)
        for section in sections:
            if "," in section:
                teacher = section[section.find(',')+2:]
                #print "teacher here" + teacher
                if teacher.upper() == thisTeacher:
                    teachersClasses[section[:section.find(',')]]=sections[section]
                    codes.append(doc['code'])
                    #print "SUCCESS"
                #else:
                    #print "this: " + thisTeacher
                    #print "other: " + teacher
        #print doc
    x = db.classes.find({'teacher':teacher})
    classes = []
    #print "teacher's Classes: " + str(teachersClasses)
    if (x == None):
        flash("This teacher has no classes")
        return redirect("/")
    '''teachersClasses = {}
    for y in x:
        print "teacher document: " + str(y)
        code = y['code']
        print "code: " + code
        sections = y['sections']
        print "sections: " + str(sections)
        for section in sections:
            teachersClasses[section]=code
            print "section: " + str(section)
    '''
    #print "teacher's classes: " + str(teachersClasses)
    #print "codes: " + str(codes)
    periods = {}
    #print "ok till here"
    '''for i in x:
        print "i"
        code = i['code']
        print "teacher code: " + str(code)
        #classes.append(i['code']+i['ext'])
        #if 'period' in i:
        #periods[c['period']] = i        '''
    #print "end for in teacher"
    if codes==[]:
        #return "your search yielded no results"
        flash ("Your search yielded no results")
        return redirect("/")        
    return render_template("teacher.html", classes=teachersClasses, teacher = thisTeacher.title(), codes=codes, L = list(set(classes)), D = periods)

@app.route("/student/<username>")
def studentpage(username):
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    username = username.replace("%20"," ")
    if (username == session['user']):
        return redirect(url_for("schedule"))
    x = db.users.find_one({'name':username})

    #for i in db.classes.find():
    #print i

    if (x == None or 'sch_list' not in x.keys()):
        flash("Student does not exist")
        return redirect("/")

    periods = {}
    teachers = {}

    for i in x['sch_list']:
        c = db.classes.find_one({'code': i[:-2], 'ext': i[-2:]})
        if 'period' in c:
            periods[c['period']] = i        
            teachers[c['period']] = c['teacher']

    return render_template("schedule.html", L = list(set(x['sch_list'])), D = periods, T = teachers)
    

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/login",methods=["GET","POST"])
def login():
    #db.classes.remove()
    #db.users.remove()
    #db.users.update({}, {'$set':{'messages':[]}}, multi=True)
    #db.users.update({},{'$set':{'confirmed':0}}, multi=True)
    #for x in db.classes.find():
        #if x['messages']!=[]:
        #print 'YESYESYESYES'
        #print "class: " + str(x)
    if 'user' in session:
        return redirect(url_for("loggedin"))
    #LOG IN
    if request.method=="POST" and request.form.get("h")!="bleh":
        button = request.form.get("sub",None)
        excl=request.form.get("ex",None)
        username = request.form.get("username", None)
        username2 = request.form.get("user",None)
        passw = request.form.get("password", None)
        error = None     
        loginfo = { 'name': username, 'pword': passw }
        if (excl != None): 
            return redirect(url_for('exclusive', user=username2))
        #CHECK IF USERNAME/PASSWORD VALID
        if db.users.find_one ( { 'name' : username , 'pword' : passw } ) != None:
	    #for x in db.users.find({'name': username,'pword':passw}):
            #print "bleh" + str(db.users.find({'name':username,'pword':passw}))
            session['user']=username

            x = db.users.find_one({'name':username, 'confirmed':1})
            if (x == None):
                flash("Please add your schedule")
                return redirect(url_for("loggedin"))
            else:
                return redirect(url_for("home"))
        #INCORRECT LOGIN INFO
        else:
            flash("incorrect login info")
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route("/loggedin", methods=["GET", "POST"])
def loggedin():
    print "loggedin"
    for x in db.classes.find():
        print x
    username = session['user']
    #PICTURE/TEXT UPLOADED BY USER
    if request.method=="POST" and request.form.get("h")=="bleh":
        ###Screenshotting works if you zoom in to make your schedule fit the entire window
        file = request.files['pic']
        username = session['user']
        uploaded = request.form.get("pic")
        #print "file: " + str(uploaded)
        boo = uploaded!=None
        #print boo
        #CHECK IF IMAGE UPLOADED
        if file and allowed_file(file.filename):
            #print "allowed file"
            q = db.users.find()
            for x in q:
                print "user: " + str(x)
            q = db.users.find_one({'name':username})
            #print 'q: ' + str(q)
            n = q['n']
            #print "n: " + str(n)
            q['n'] = n + 1
            db.users.update({'name':username}, {'$inc': {'n': 1}})
            #print "image"
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            newFileName = username + str(n) + ".jpg"
            #print "newFileName: " + newFileName
            session['img'] = newFileName
            os.rename("static/"+file.filename, "static/" + newFileName)
            return redirect(url_for("crop"))
        #CHECK IF TEXT PASTED
        elif request.form.get("txtsched") != "":
            schedule = request.form.get("txtsched")
            session['sched'] = schedule
            #print "text pasted: " + schedule
        else:
            #return "Something went wrong, you shouldn't be here"
            flash ("Please upload a schedule")
            return (redirect(url_for("loggedin")))
        #print "redirect confirm"
        return redirect(url_for('confirm'))
    elif db.users.find_one({'name':username, 'confirmed':1}) != None:
        #print "redirect schedule"
        return redirect(url_for("schedule"))
    #LOGGING IN FOR THE FIRST TIME/LOGGING IN WITHOUT CONFIRMING/UPLOADING SCHEDULE
    else:
        #print "render loggedin"
        return render_template("loggedin.html", username=username, n=0)


@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        button = request.form.get("sub", None)
        username = request.form.get("username", None)
        passw = request.form.get("password", None)
        error = None
        if db.users.find_one ( { 'name' : username } ) == None:
            if username == "":
                flash("Please enter a username")
                return redirect(url_for('register'))
            if passw == "":
                flash("Please enter a password")
                return redirect(url_for('register'))
            db.users.insert ( { 'name': username, 'pword': passw, 'schedule': 0, 'confirmed': 0, 'n': 0, 'messages': []} )
            flash("Thanks for joining! Please log in now.")
            return redirect(url_for('login'))
        else:
            flash("Please select an available username")
            return redirect(url_for('register'))
    return render_template("register.html")

@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if request.method=="POST":
        print "confirm method = post"
        f = request.form.get("f")
        #print "format: " + f
        schedule = request.form.get("scheduleCodes")
        schedule = schedule.split("\n")
        #print "schedule obtained"
        scheduleSections = request.form.get("scheduleSections")
        #print "sections obtained"
        scheduleSections = scheduleSections.split("\n")
        teachers = request.form.get("scheduleTeachers")
        #print "teachers obtained"
        teachers = teachers.split("\n")
        periods = request.form.get("schedulePeriods")
        periods = periods.split("\n")
        titles = request.form.get("scheduleTitles")
        titles = titles.split("\n")
        username = session['user']
        #print "username obtained"
        sch_list = []
        #print "in confirm: " + str(schedule)
        #print str(range(10))
        #print schedule
        usersClasses = []
        for i in range(len(schedule)-1):
            #print "i in range" + str(i)
            #CHECK TO SEE IF SOMEONE UPLOADED SCHEDULE WITH SAME CLASS
            #print "q success: " + str(q)
            #print q == None
            code = "".join(schedule[i].strip())
            q = db.classes.find_one({'code':code})
            usersClasses.append(code)
            if q == None:
                #print "q == none"
                if f == "pd":
                    #print "q pd"
                    #print "sched[i]: " + schedule[i]
                    #print "title[i]: " + titles[i]
                    #print "pd[i]: " + periods[i]
                    title = "".join(titles[i].strip())
                    period = "".join(periods[i].strip())
                    section = 'pd' + "".join(periods[i].strip())
                    db.classes.insert({'code':code, 'title':title, 'sections': {'pd'+period:[username]}})
                    #print "insert successful"
                elif f == "class":
                    #print "q class"
                    #print "sched[i]: " + schedule[i]
                    #print "teacher[i]: " + teachers[i]
                    #print "section[i]: " + scheduleSections[i]
                    teacher = "".join(teachers[i].strip())
                    section = 'section'+"".join(scheduleSections[i].strip())+", "+teacher
                    print "section after: " + section
                    print "section before: " + 'section' + scheduleSections[i]+', '+teachers[i]
                    db.classes.insert({'code':code, 'sections': {section:[username]}})
                    #print "insert successful"
                #else:
                #print "error in db classes loop"
            else:
                if f == "pd":
                    #update classes to include user in q['pd'][pd#]
                    #print "q exists, pd"
                    qPeriods = q['sections']
                    title = "".join(titles[i].strip())
                    #print "qPeriods: " + str(qPeriods)
                    #print str(periods[i])
                    period = "pd" + "".join(periods[i].strip())
                    if period in qPeriods.keys():
                        usersInQPeriods = qPeriods[period]
                        usersInQPeriods.append(username)
                    else:
                        qPeriods[period] = [username]
                    db.classes.update({'code':code}, {'$set': {'sections': qPeriods, 'title': title}})
                elif f == "class":
                    #print "sections: " + str(q['sections'])
                    qSections = q['sections']
                    #print "qSections: " + str(qSections)
                    #print str(scheduleSections[i])
                    teacher = "".join(teachers[i].strip())
                    print "teacher before updating classes: " + teacher
                    print "teacherlist item: " + teachers[i]
                    section = "section"+"".join(scheduleSections[i].strip())+", "+teacher
                    if section in qSections.keys():
                        usersInQSections = qSections[section]
                        #print "users in section: " + str(usersInQSections)
                        usersInQSections.append(username)
                        #print str(qSections)
                    else:
                        qSections[section] = [username]
                    #print "updating with: " + str(qSections)
                    db.classes.update({'code':code}, {'$set': {'sections': qSections}})
                    #for x in db.classes.find({'code':schedule[i]}):
                    #print str(x)
                    #print "q exists, class"
            #print "end of iteration"
        print usersClasses
        #print str(db.users.find_one({'name':username}))
        #print "for loop successfully ended"
        '''for i in db.classes.find({'code':'ZLN5'}):
        i['period'] = int(i['ext']) + 3
        db.classes.save(i)'''
        #print "HELLO"
        confirmed = request.form.get("confirm", None)
        back = request.form.get("back", None)
        #print "conf"
        if confirmed != None:
            db.users.update({'name':username}, {'$set': {'schedule':usersClasses}})
            db.users.update({'name':username}, {'$set':{'confirmed':1}})
            #print "conf"
            return redirect(url_for("schedule"))
        elif back != None:
            #print "redirect loggedin"
            return redirect(url_for("loggedin"))
        #return render_template("loggedin.html")
        #else:
        #return "error"
    elif request.method=="POST" and request.form.get("sub")=="Go Back":
        return redirect(url_for("crop"))
    username = session['user']
    schedule = session['sched']
    #print "render in confirm: " + schedule
    #print "end schedule"
    scheduleCodes = []
    schedulePeriods = []
    scheduleSections = []
    scheduleTeachers = []
    scheduleTitles = []
    formatOfFile = checkFormat(schedule.split("\n")[0])
    #print "format: " + formatOfFile
    if formatOfFile == "class":
        #print "format == class"
        for s in schedule.split("\n")[1:]:
            ' '.join(s.split())
            if len(s.split())>=3:
                #print "s: " + s
                scheduleCodes.append(s.split()[0])
                scheduleSections.append(s.split()[1])
                scheduleTeachers.append(join(s.split()[2:]))
            #else:
            #print "s<3: " + s
        #print "class section teacher format"
        #print "\n".join(scheduleTeachers)
        st = ""
        for s in scheduleTeachers:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            st = st + tmp + "\n"
        #print "\n".join(scheduleSections)
        ss = ""
        for s in scheduleSections:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            ss = ss + tmp + "\n"
        sc = ""
        #print "\n".join(scheduleCodes)
        for s in scheduleCodes:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            sc = sc + tmp + "\n"
        #print "st: " + st
        #print "ss: " + ss
        #print "sc: " + sc
        #print "render confirm"
        return render_template("confirmschedule.html", schedulePeriods='null', scheduleTeachers=st, scheduleSections=ss, scheduleCodes=sc, scheduleTitles='null', username=username, f='class')
    elif formatOfFile == "pd":
        #print "format === pd"
        #print "sched: " + str(schedule)
        #print "pd code title"
        #print "ord: " + str(ord("_"))
        for s in schedule.split("\n")[1:]:
            ' '.join(s.split())
            if len(s.split())>=3:
                #print s
                schedulePeriods.append(s.split()[0])
                scheduleCodes.append(s.split()[1])
                scheduleTitles.append(join(s.split()[2:]))
            #else:
            ##print "s<3: " + s
        #print "pds: " + str(schedulePeriods)
        sp = ""
        for s in schedulePeriods:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            sp = sp + tmp + "\n"
        #print "codes: " + str(scheduleCodes)
        sc = ""
        for s in scheduleCodes:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            sc = sc + tmp + "\n"
        #print "titles: " + str(scheduleTitles)
        st = ""
        for s in scheduleTitles:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            st = st + tmp + "\n"
        return render_template("confirmschedule.html", schedulePeriods=sp, scheduleTeachers='null', scheduleSections='null', scheduleCodes=sc, scheduleTitles=st, username=username, f='pd')

    else:
        #return "cropping failed, please try manual input"
        flash("Please include the heading class/teacher/section or pd/title/code in your entry")
        return redirect(url_for('loggedin'))
    #print "render confirm, shouldnt be here"
    return render_template("confirmschedule.html", schedulePeriods='null', scheduleTeachers='null', scheduleSections='null', scheduleCodes='null', username=username)

@app.route("/analyzeSchedule/<username>/<schedule>", methods=["GET", "POST"])
def analyzeSchedule(username, schedule):
    return render_template("loggedinwithschedule.html", username=username, n=0, schedule=schedule)

@app.route("/logout")
def logout():
    #print "logout"
    del session['user']
    return redirect(url_for('home'))

@app.route("/crop", methods=["GET", "POST"])
def crop():
    print "/crop"
    username = session['user']
    newFileName = session['img']
    #print newFileName
    #this saves the cropped image
    if request.method=="POST" and request.form.get("sub")=="Crop Image":
        print "crop image"
        username = session['user']
        url = 'http://104.236.74.79/StuyApp/templates/bs.php?'
        x = "x=" + request.form.get("x")
        y = "y=" + request.form.get("y")
        w = "w=" + request.form.get("w")
        h = "h=" + request.form.get("h")
        s = "source=../static/" + newFileName
        url = url + x + "&" + y + "&" + w + "&" + h + "&submit=submit" + "&" + s
        #run this on server, image will be saved there
        #print "use url: " + url
        r = urllib2.urlopen(url)
        #print "urllib works"
        img = Image.open("templates/images/tst.jpg")
        #print "post"
        try :
            schedule = image_to_string(img)
            os.remove("static/"+newFileName)
        except :
            #return "schedule could not be read, please try again"
            flash ("Schedule could not be read, please try again")
            return redirect(url_for("loggedin"))
        #print "no error in pytesser"
        session['sched']=schedule
        #print "image posted: " + schedule
        return redirect(url_for("confirm"))
    elif request.method=="POST" and request.form.get("sub")=="Back":
        return redirect(url_for("loggedin"))
    else:
        #print "before crop: " + newFileName
        return render_template("crop.html", img=newFileName)

@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method=="POST":
        file = request.files['pic']        
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        newFileName = "a1.jpg"
        #print "newFileName: " + newFileName
        os.rename("static/"+file.filename, "static/" + newFileName)
        return render_template("test.html", src='../static/a1.jpg')
        url = 'http://104.236.74.79/StuyApp/templates/bs.php?'
        x = "x=" + request.form.get("x")
        y = "y=" + request.form.get("y")
        w = "w=" + request.form.get("w")
        h = "h=" + request.form.get("h")
        url = url + x + "&" + y + "&" + w + "&" + h + "&submit=submit"
        r = urllib2.urlopen(url)
    else:
        ###Screenshotting works if you zoom in to make your schedule fit the entire window
        img = Image.open("blah/scheduleforfinalproject.jpg")
        sampleScheduleForTesting = """EES 02 SCHECHTER
HES 04 MCROYMENDELL 
HLS 01 WEISSMAN 
HVS 06 TRAINOR 
MQS 01 BROOKS 
PES 01 CHOY 
SQS 01 REEP 
ZLN 05 GEL LOWE 
ZQT 01 SPORTS TEAM"""
        s = ""
        wordsList = []
        for x in sampleScheduleForTesting:
            if x == " ":
                #print s
                wordsList.append(s)
                s = ""
            else:
                s += x
        wordsList.append(s)
        eachLine = []
        i = len (wordsList) - 1
        numIndeces = []
        while i >= 0:
            word = wordsList[i]
            try:
                int(word)
                numIndeces.append(i)
                #print word + "is a number"
            except:
                break
                #print word + "not number"
            i = i - 1
        tempList = []
        tempList.append(wordsList[numIndeces[0]-1])
        tempList.append(wordsList[numIndeces[0]])
        j = numIndeces[0] + 1
        s = ""
        while j < len(wordsList):
            s = s + wordsList[j] + " "
            j = j + 1
        tempList.append(s[:-1])
        #print tempList
        for k in range (numIndeces[0], len(wordsList)):
            s += wordsList[k] + " "
        j = 1
        allClasses = []
        while j < len(numIndeces):
            tempList = []
            tempList.append(wordsList[numIndeces[j]-1])
            tempList.append(wordsList[numIndeces[j]])
            s = ""
            for k in range (numIndeces[j]+1, numIndeces[j-1]-1):
                s = s + wordsList[k] + " "
            tempList.append(s[:-1])
            #print tempList
            allClasses.append(tempList)
            #print wordsList[numIndeces[j-1]-1]
            j = j + 1
        db.students.insert({'name':'adduserlater', 'id':1847, 'classes': allClasses})
        #print allClasses
        #for x in db.students.find():
        #print x
        return render_template("test.html", src='../static/a1.jpg')

if __name__== "__main__":
    #db.users.insert({'name':'b','pword':'b'})

    '''for i in db.users.find():
        print i
    for i in db.classes.find():
        print i'''

    app.debug = True
    app.run(port=5555,extra_files="/static/*")
