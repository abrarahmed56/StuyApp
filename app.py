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
    return render_template("home.html", logged = 'user' in session)

@app.route("/about")
def about():
    return render_template("about.html", logged = 'user' in session)

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    for x in db.classes.find():
        print x
        c = x['code']
        for y in db.classes.find({'code':c}):
            print "same code: " + str(y)
        print '\n'
    print "method schedule"
    username = session['user']
    print "user in session"
    if request.method == "POST":
        print "schedule method = post"
        db.users.update({"name":username},{'$set':{'confirmed':0}})
        #remove name from classes
        return redirect(url_for("loggedin"))
    print "schedule"
    x = db.users.find_one({'name':username})

    #for i in db.classes.find():
    #print i
    print "schedule2"
    if (x == None or 'sch_list' not in x.keys()):
        flash("Please add your schedule")
        print x.keys()
        return redirect(url_for("loggedin"))

    periods = {}
    teachers = {}

    print "checkerror"
    for i in x['sch_list']:
        print i

    print "checkerror2"
    q = db.users.find_one({'name':username})
    print str(q)
    schedule = q['schedule']
    titles = []
    periods = []
    sections = []
    teachers = []
    print range(len(schedule))
    for i in range(len(schedule)):
        print 'i in schedule: ' + str(i)
        qu = db.classes.find_one({'code':schedule[i]})
        print "q: " + str(qu)
        if 'title' in qu:
            title = qu['title']
            print 'title in qu: ' + title
            titles.append(title)
        else:
            titles.append("")
        if 'teacher' in qu:
            teacher = qu['teacher']
            print 'teacher in q: ' + teacher
            teachers.append(teacher)
        else:
            teachers.append("")
        print 'title/teacher done'
        que = qu['sections']
        for pdorsection in que:
            print "period or section: " + pdorsection
            if pdorsection[:2]=="pd":
                period = que[pdorsection]
                print "people in pd: " + str(period)
                if username in period:
                    periods.append(pdorsection)
                    sections.append("")
                else:
                    periods.append("")
            else:
                section = que[pdorsection]
                print "people in section: " + str(section)
                if username in section:
                    print "usr in period"
                    sections.append(pdorsection)
                    periods.append("")
                else:
                    print "else"
                    periods.append("")
    print str(q)
    print "codes: " + str(schedule)
    print "teachers: " + str(teachers)
    print "titles: " + str(titles)
    print "sections: " + str(sections)
    print "periods: " + str(periods)
    return render_template("schedule2.html", L = schedule, D = schedule, T = teachers, titles=titles, periods=periods, teachers=teachers, sections=sections, col1="Code", col2="Class", col3="Teacher", col4="Section", col5="Period", schedule=schedule)

@app.route("/class/<code>")
def classpage(code):
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    code = code.replace("%20"," ")
    q = db.classes.find_one({'code':code+"\r"})
    #y = db.classes.find({'code':code[:-2]})
    for x in db.classes.find():
        print "x"
        print x['code']
    print "code: " + code
    print "q: " + str(q)
    classList = q['sections']
    print "classList: " + str(classList)
    studentsInClass = {}
    for x in classList:
        print "element in classlist: " + x
        print "class[x]" + str(classList[x])
        studentsInClass[x]=classList[x]
        print studentsInClass
    teacher = q['teacher']
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

    return render_template("class.html", code=code, similar = [], students = studentsInClass, teacher = teacher)

@app.route("/teacher/<teacher>")
def teacherpage(teacher):
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    teacher = teacher.replace("%20"," ")
    x = db.classes.find({'teacher':teacher+'\r'})
    classes = []
    if (x == None):
        flash("This teacher has no classes")
        return redirect("/")
    teachersClasses = {}
    for y in x:
        print "teacher document: " + str(y)
        code = y['code']
        print "code: " + code
        sections = y['sections']
        print "sections: " + str(sections)
        for section in sections:
            teachersClasses[section]=code
            print "section: " + str(section)
    print "teacher's classes: " + str(teachersClasses)
    periods = {}
    print "ok till here"
    for i in x:
        print "i"
        code = i['code']
        print "teacher code: " + str(code)
        #classes.append(i['code']+i['ext'])
        #if 'period' in i:
        #periods[c['period']] = i        
    print "end for in teacher"
    return render_template("teacher.html", classes=teachersClasses, teacher = teacher.title(), L = list(set(classes)), D = periods)

@app.route("/student/<username>")
def studentpage(username):
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    username = username.replace("%20"," ")
    if (username == session['user']):
        return redirect(url_for("schedule"))
    x = db.users.find_one({'name':username})

    for i in db.classes.find():
        print i

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
    db.users.update({},{'$set':{'confirmed':0}})
    db.classes.remove()
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
	    for x in db.users.find({'name': username,'pword':passw}):
	        print "bleh" + str(db.users.find({'name':username,'pword':passw}))
            session['user']=username

            x = db.users.find_one({'name':username, 'confirmed':1})
            if (x == None):
                flash("Please add your schedule")
                return redirect(url_for("loggedin"))
            else:
                return redirect(url_for("schedule"))
        #INCORRECT LOGIN INFO
        else:
            flash("incorrect login info")
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route("/loggedin", methods=["GET", "POST"])
def loggedin():
    username = session['user']
    #PICTURE/TEXT UPLOADED BY USER
    if request.method=="POST" and request.form.get("h")=="bleh":
        ###Screenshotting works if you zoom in to make your schedule fit the entire window
        file = request.files['pic']
        username = session['user']
        uploaded = request.form.get("pic")
        print "file: " + str(uploaded)
        boo = uploaded!=None
        print boo
        #CHECK IF IMAGE UPLOADED
        if file and allowed_file(file.filename):
            print "allowed file"
            q = db.users.find()
            for x in q:
                print "user: " + str(x)
            q = db.users.find_one({'name':username})
            print 'q: ' + str(q)
            n = q['n']
            print "n: " + str(n)
            q['n'] = n + 1
            db.users.update({'name':username}, {'$inc': {'n': 1}})
            print "image"
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            newFileName = username + str(n) + ".jpg"
            print "newFileName: " + newFileName
            session['img'] = newFileName
            os.rename("static/"+file.filename, "static/" + newFileName)
            return redirect(url_for("crop"))
        #CHECK IF TEXT PASTED
        elif request.form.get("txtsched") != "":
            schedule = request.form.get("txtsched")
            session['sched'] = schedule
            print "text pasted: " + schedule
        else:
            return "Something went wrong, you shouldn't be here"
        print "redirect confirm"
        return redirect(url_for('confirm'))
    elif db.users.find_one({'name':username, 'confirmed':1}) != None:
        print "redirect schedule"
        return redirect(url_for("schedule"))
    #LOGGING IN FOR THE FIRST TIME/LOGGING IN WITHOUT CONFIRMING/UPLOADING SCHEDULE
    else:
        print "render loggedin"
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
            db.users.insert ( { 'name': username, 'pword': passw, 'schedule': 0, 'confirmed': 0, 'n': 0} )
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
        print "format: " + f
        schedule = request.form.get("scheduleCodes")
        schedule = schedule.split("\n")
        print "schedule obtained"
        scheduleSections = request.form.get("scheduleSections")
        print "sections obtained"
        scheduleSections = scheduleSections.split("\n")
        teachers = request.form.get("scheduleTeachers")
        print "teachers obtained"
        teachers = teachers.split("\n")
        periods = request.form.get("schedulePeriods")
        periods = periods.split("\n")
        titles = request.form.get("scheduleTitles")
        titles = titles.split("\n")
        username = session['user']
        print "username obtained"
        sch_list = []
        print "in confirm: " + str(schedule)
        print str(range(10))
        print schedule
        usersClasses = []
        for i in range(len(schedule)-1):
            print "i in range" + str(i)
            #CHECK TO SEE IF SOMEONE UPLOADED SCHEDULE WITH SAME CLASS
            q = db.classes.find_one({'code':schedule[i]})
            print "q success: " + str(q)
            usersClasses.append(schedule[i])
            print q == None
            if q == None:
                print "q == none"
                if f == "pd":
                    print "q pd"
                    print "sched[i]: " + schedule[i]
                    print "title[i]: " + titles[i]
                    print "pd[i]: " + periods[i]
                    db.classes.insert({'code':schedule[i], 'title':titles[i], 'sections': {'pd'+periods[i]:[username]}})
                    print "insert successful"
                elif f == "class":
                    print "q class"
                    print "sched[i]: " + schedule[i]
                    print "teacher[i]: " + teachers[i]
                    print "section[i]: " + scheduleSections[i]
                    db.classes.insert({'code':schedule[i], 'teacher':teachers[i], 'sections': {'section'+scheduleSections[i]:[username]}})
                    print "insert successful"
                else:
                    print "error in db classes loop"
            else:
                if f == "pd":
                    #update classes to include user in q['pd'][pd#]
                    print "q exists, pd"
                    qPeriods = q['sections']
                    print "qPeriods: " + str(qPeriods)
                    print str(periods[i])
                    if "pd"+periods[i] in qPeriods.keys():
                        usersInQPeriods = qPeriods["pd"+periods[i]]
                        usersInQPeriods.append(username)
                    else:
                        qPeriods["pd"+periods[i]] = [username]
                    db.classes.update({'code':schedule[i]}, {'$set': {'sections': qPeriods}})
                elif f == "class":
                    print "sections: " + str(q['sections'])
                    qSections = q['sections']
                    print "qSections: " + str(qSections)
                    print str(scheduleSections[i])
                    if "section"+scheduleSections[i] in qSections.keys():
                        usersInQSections = qSections["section"+scheduleSections[i]]
                        print "users in section: " + str(usersInQSections)
                        usersInQSections.append(username)
                        print str(qSections)
                    else:
                        qSections[scheduleSections[i]] = [username]
                    print "updating with: " + str(qSections)
                    db.classes.update({'code':schedule[i]}, {'$set': {'sections': qSections}})
                    for x in db.classes.find({'code':schedule[i]}):
                        print str(x)
                    print "q exists, class"
            print "end of iteration"
        print usersClasses
        db.users.update({'name':username}, {'$set': {'schedule':usersClasses}})
        print str(db.users.find_one({'name':username}))
        print "for loop successfully ended"
        for i in db.classes.find({'code':'ZLN5'}):
            i['period'] = int(i['ext']) + 3
            db.classes.save(i)
        print "HELLO"
        confirmed = request.form.get("confirm", None)
        back = request.form.get("back", None)
        print "conf"
        if confirmed != None:
            print "conf"
            return redirect(url_for("schedule"))
        elif back != None:
            print "redirect loggedin"
            return redirect(url_for("loggedin"))
            #return render_template("loggedin.html")
        else:
            return "error"
    username = session['user']
    schedule = session['sched']
    print "render in confirm: " + schedule
    print "end schedule"
    scheduleCodes = []
    schedulePeriods = []
    scheduleSections = []
    scheduleTeachers = []
    scheduleTitles = []
    formatOfFile = checkFormat(schedule.split("\n")[0])
    print "format: " + formatOfFile
    if formatOfFile == "class":
        print "format == class"
        for s in schedule.split("\n")[1:]:
            ' '.join(s.split())
            if len(s.split())>=3:
                print "s: " + s
                scheduleCodes.append(s.split()[0])
                scheduleSections.append(s.split()[1])
                scheduleTeachers.append(join(s.split()[2:]))
            else:
                print "s<3: " + s
        print "class section teacher format"
        print "\n".join(scheduleTeachers)
        st = ""
        for s in scheduleTeachers:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            st = st + tmp + "\n"
        print "\n".join(scheduleSections)
        ss = ""
        for s in scheduleSections:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            ss = ss + tmp + "\n"
        sc = ""
        print "\n".join(scheduleCodes)
        for s in scheduleCodes:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            sc = sc + tmp + "\n"
        print "st: " + st
        print "ss: " + ss
        print "sc: " + sc
        print "render confirm"
        return render_template("confirmschedule.html", schedulePeriods='null', scheduleTeachers=st, scheduleSections=ss, scheduleCodes=sc, scheduleTitles='null', username=username, f='class')
    elif formatOfFile == "pd":
        print "format === pd"
        print "sched: " + str(schedule)
        print "pd code title"
        print "ord: " + str(ord("_"))
        for s in schedule.split("\n")[1:]:
            ' '.join(s.split())
            if len(s.split())>=3:
                print s
                schedulePeriods.append(s.split()[0])
                scheduleCodes.append(s.split()[1])
                scheduleTitles.append(join(s.split()[2:]))
            else:
                print "s<3: " + s
        print "pds: " + str(schedulePeriods);
        sp = ""
        for s in schedulePeriods:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            sp = sp + tmp + "\n"
        print "codes: " + str(scheduleCodes)
        sc = ""
        for s in scheduleCodes:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            sc = sc + tmp + "\n"
        print "titles: " + str(scheduleTitles)
        st = ""
        for s in scheduleTitles:
            tmp = ""
            for c in s:
                if ord(c) < 128:
                    tmp = tmp + c
            st = st + tmp + "\n"
        return render_template("confirmschedule.html", schedulePeriods=sp, scheduleTeachers='null', scheduleSections='null', scheduleCodes=sc, scheduleTitles=st, username=username, f='pd')

    else:
        return "cropping failed, please try manual input"
    print "render confirm, shouldnt be here"
    return render_template("confirmschedule.html", schedulePeriods='null', scheduleTeachers='null', scheduleSections='null', scheduleCodes='null', username=username)

@app.route("/analyzeSchedule/<username>/<schedule>", methods=["GET", "POST"])
def analyzeSchedule(username, schedule):
    return render_template("loggedinwithschedule.html", username=username, n=0, schedule=schedule)

@app.route("/logout")
def logout():
    print "logout"
    del session['user']
    return redirect(url_for('home'))

@app.route("/crop", methods=["GET", "POST"])
def crop():
    print "crop"
    username = session['user']
    newFileName = session['img']
    print newFileName
    #this saves the cropped image
    if request.method=="POST":
        username = session['user']
        url = 'http://104.236.74.79/StuyApp/templates/bs.php?'
        x = "x=" + request.form.get("x")
        y = "y=" + request.form.get("y")
        w = "w=" + request.form.get("w")
        h = "h=" + request.form.get("h")
        s = "source=../static/" + newFileName
        url = url + x + "&" + y + "&" + w + "&" + h + "&submit=submit" + "&" + s
        #run this on server, image will be saved there
        r = urllib2.urlopen(url)
        img = Image.open("templates/images/tst.jpg")
        print "post"
        try :
            schedule = image_to_string(img)
            os.remove("static/"+newFileName)
        except :
            return "schedule could not be read, please try again"
        print "no error in pytesser"
        session['sched']=schedule
        print "image posted: " + schedule
        return redirect(url_for("confirm"))
    else:
        print "before crop: " + newFileName
        return render_template("crop.html", img=newFileName)

@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method=="POST":
        file = request.files['pic']        
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        newFileName = "a1.jpg"
        print "newFileName: " + newFileName
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
                print s
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
                print word + "is a number"
            except:
                print word + "not number"
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
        print tempList
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
            print tempList
            allClasses.append(tempList)
            print wordsList[numIndeces[j-1]-1]
            j = j + 1
        db.students.insert({'name':'adduserlater', 'id':1847, 'classes': allClasses})
        print allClasses
        for x in db.students.find():
            print x
        return render_template("test.html", src='../static/a1.jpg')

if __name__== "__main__":
    db.users.insert({'name':'b','pword':'b'})

    for i in db.users.find():
        print i
    for i in db.classes.find():
        print i

    app.debug = True
    app.run(port=5555,extra_files="/static/*")
