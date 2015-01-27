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

@app.route("/schedule")
def schedule():
    username = session['user']
    x = db.users.find_one({'name':username})

    for i in db.classes.find():
        print i

    if (x == None or 'sch_list' not in x.keys()):
        flash("Please add your schedule")
        return redirect("/")

    periods = {}
    teachers = {}
    t_2 = []

    for i in list(set(x['sch_list'])):
        c = db.classes.find_one({'code': i[:-2], 'ext': i[-2:]})
        t_2.append(c['teacher'])
        if 'period' in c:
            periods[c['period']] = i        
            teachers[c['period']] = c['teacher']

    return render_template("schedule2.html", L = list(set(x['sch_list'])), D = periods, T = teachers, T2 = t_2)

@app.route("/class/<code>")
def classpage(code):
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    code = code.replace("%20"," ")
    x = db.classes.find_one({'code':code[:-2],'ext': code[-2:]})
    y = db.classes.find({'code':code[:-2]})

    if (x == None):
        return "This class does not exist"

    similar = []
    for i in y:
        similar.append(i['ext'])
    students = x['students']
    if 'period' in x:
        period = x['period']
    else:
        period = "Unknown"
    teacher = x['teacher']

    return render_template("class2.html", code=code, similar = similar, students = students, period = period, teacher = teacher)

@app.route("/teacher/<teacher>")
def teacherpage(teacher):
    if 'user' not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    teacher = teacher.replace("%20"," ")
    x = db.classes.find({'teacher':teacher})
    classes = []
    
    if (x == None):
        flash("This teacher has no classes")
        return redirect("/")

    periods = {}

    for i in x:
        classes.append(i['code']+i['ext'])
        if 'period' in i:
            periods[i['period']] = i['code']+i['ext']        
    
    return render_template("teacher2.html", teacher = teacher.title(), L = list(set(classes)), D = periods)

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
        flash("Please add your schedule")
        return redirect("/")

    periods = {}
    teachers = {}
    t_2 = []

    for i in list(set(x['sch_list'])):
        c = db.classes.find_one({'code': i[:-2], 'ext': i[-2:]})
        t_2.append(c['teacher'])
        if 'period' in c:
            periods[c['period']] = i        
            teachers[c['period']] = c['teacher']

    return render_template("schedule2.html", L = list(set(x['sch_list'])), D = periods, T = teachers, T2 = t_2)

@app.route("/search")
def search():
    select = request.args.get("select")
    search = request.args.get("search")
    
    return redirect("/"+select+"/"+search)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/login",methods=["GET","POST"])
def login():
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

            x = db.users.find_one({'name':username})
            if (x == None or 'sch_list' not in x.keys()):
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
            sch_list = []
            for i in schedule.split("\n"):
                if (i != ""):
                    sch_list.append(i.split()[0]+i.split()[1])
                    db.classes.update(
                        {'code':i.split()[0], 'ext':i.split()[1], 'teacher':join(i.split()[2:])},
                        {'$addToSet': {'students':username}}, 
                        True)

            db.users.update({'name':username}, {'$set': {
                'schedule':schedule.split("\n"),
                'sch_list':sch_list}})

            for i in db.classes.find({'code':'ZLN5'}):
                i['period'] = int(i['ext']) + 3
                db.classes.save(i)

            return redirect(url_for("schedule"))

    elif db.users.find_one({'name':username, 'confirmed':1}) != None:
        return redirect(url_for("schedule"))
    else:
        return render_template("loggedin.html", username=username, n=0)


@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        button = request.form.get("sub", None)
        username = request.form.get("username", None)
        passw = request.form.get("password", None)
        error = None
        #db.users.remove()
        if db.users.find_one ( { 'name' : username } ) == None:
            if username == "":
                flash("Please enter a username")
                return redirect(url_for('register'))
            if passw == "":
                flash("Please enter a password")
                return redirect(url_for('register'))
            db.users.insert ( { 'name': username, 'pword': passw, 'schedule': 0, 'confirmed': 0, 'n': 0} )
            #return "<h1>Thanks for joining!</h1>" + str ( { 'name':username, 'pword': passw } )
            flash("Thanks for joining! Please log in now.")
            return redirect(url_for('login'))
        else:
            flash("Please select an available username")
            #return "<h1>Please select an available username</h1>"
            return redirect(url_for('register'))
    return render_template("register.html",url2="/login",link2="Login",url0="/",link0="Home",url1="/about",link1="About")

@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if request.method=="POST":
        print "HELLO"
        confirmed = request.form.get("confirm", None)
        back = request.form.get("back", None)
        print "conf"
        if confirmed != None:
            print "conf"
            return redirect(url_for("schedule"))
        elif back != None:
            return redirect(url_for("loggedin"))
            #return render_template("loggedin.html")
    username = session['user']
    #q = db.users.find_one({'name':username})
    #schedule = q['sch_list']
    return render_template("confirmschedule.html", schedule=schedule)
    #db.users.update({'name':username}, {'$set':{'confirmed':1}})
    #return redirect(url_for('analyzeSchedule',username=username, schedule=schedule))
    #else:
    #return "dont enter this url"

@app.route("/analyzeSchedule/<username>/<schedule>", methods=["GET", "POST"])
def analyzeSchedule(username, schedule):
    return render_template("loggedinwithschedule.html", username=username, n=0, url1="/exclusive", link1="Exclusively for Users", url2="/logout", link2="Logout", schedule=schedule)

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
        return redirect(url_for("schedule"))
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
    #db.users.remove()
    #db.classes.remove()
    #db.users.insert({'name':'b','pword':'b'})
    #db.classes.insert({'code':'ZLN5','ext':'03','students':[],'teacher':'MESSE TARVIN','period':6})

    for i in db.users.find():
        print i
    for i in db.classes.find():
        print i

    app.debug = True
    app.run(port=5555,extra_files="/static/*")
