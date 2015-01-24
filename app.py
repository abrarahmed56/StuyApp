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

UPLOAD_FOLDER = './tmp/'
ALLOWED_EXTENSIONS = set(['png', 'bmp', 'jpg'])

form = cgi.FieldStorage()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret"
conn = Connection()
db = conn ['stuyapp']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/")
def home(): 
    return render_template("home.html",url1="/login",link1="Login",url2="/register",link2="Register",url0="/about",link0="About")

@app.route("/schedule")
def schedule():
    username = session['user']
    print username
    x = db.users.find_one({'name':username})
    for y in db.users.find():
        print y
    print x
    if (x == None):
        flash("Please add your schedule")
        return redirect(url_for(''))
    return render_template("schedule.html", L = list(set(x['sch_list'])), S = x['sch_dict'])

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
            #return exclusive(username2)
            return redirect(url_for('exclusive', user=username2))
        #CHECK IF USERNAME/PASSWORD VALID
        if db.users.find_one ( { 'name' : username , 'pword' : passw } ) != None:
            n = db.users.update ( { 'name': username } , { '$inc': { 'n' : 1 } } )
	    #for q in db.users.find({'name':username}):
 	        #print int(str(q)[str(q).find("u'n': ")+6: str(q).rfind("}")])
	    q = db.users.find({'name':username})[0]
	    #n = int(str(q)[str(q).find("u'n': ")+6: str(q).rfind("}")])
            n = q['n']
            #n = 0
            #n = n + 1
            #session['n']=n
	    for x in db.users.find({'name': username,'pword':passw}):
	        print "bleh" + str(db.users.find({'name':username,'pword':passw}))
            session['user']=username
            #CHECK IF SCHEDULE IS UPLOADED
            if db.users.find_one({'name': username, 'schedule': 1}) != None:
                img = Image.open("tmp/"+username+".bmp")
                schedule = image_to_string(img)
                #CHECK IF SCHEDULE IS CONFIRMED
                if db.users.find_one({'name': username, 'confirmed': 1}) != None:
                    #return redirect(url_for("/analyzeSchedule", username=username, schedule=schedule))
                    return render_template("loggedinwithschedule.html", username=username, n=n, url1="/exclusive", link1="Exclusively for Users", url2="/logout", link2="Logout", schedule=schedule)
                #SCHEDULE NOT CONFIRMED YET
                else:
                    #print db.users.find()
                    #return redirect(url_for("/confirm/", username=username, schedule=schedule))
                    return render_template("confirmschedule.html", username=username, n=n, url1="/exclusive", link1="Exclusively for Users", url2="/logout", link2="Logout", schedule=schedule)
            #SCHEDULE NOT UPLOADED
            else:
                db.users.update({'name':username}, {'$set':{'schedule':1}})
                return render_template("loggedin.html", username=username, n=n,url1="/exclusive",link1="Exclusively for Users",url2="/logout",link2="Logout")
        #INCORRECT LOGIN INFO
        else:
            flash("incorrect login info")
            return redirect(url_for('login'))


    #PICTURE/TEXT UPLOADED BY USER
    elif request.method=="POST" and request.form.get("h")=="bleh":
        ###Screenshotting works if you zoom in to make your schedule fit the entire window
        file = request.files['pic']
        username = session['user']
        #CHECK IF IMAGE UPLOADED
        if file:# and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            newFileName = username + ".bmp"
            os.rename("tmp/"+file.filename, "tmp/" + newFileName)
            img = Image.open("tmp/" + newFileName)
            for x in db.users.find():
                print "mongo: " + str(x)
            db.users.update({'name':username}, {'$set':{'schedule':1}})
            schedule = image_to_string(img)
            return render_template("confirmschedule.html", username=username, url1="/exclusive", link1="Exclusively for Users", url2="/logout", link2="Logout", schedule=schedule)
        #CHECK IF TEXT PASTED
        elif request.form.get("txtsched") != "":
            sch_list = []
            for i in request.form.get("txtsched").split("\n"):
                if (i != ""):
                    print i
                    sch_list.append(i.split()[0])

            sch_list.remove('ZLN5')
            sch_dict = {str(x+1) : '' for x in range(10)}
            sch_dict['6'] = 'ZLN5'

            db.users.update({'name':username}, {'$set':{'sch_list':sch_list, 'sch_dict':sch_dict}})
            
            return redirect(url_for('schedule'))
            
        #IF NOTHING INPUT, SAMPLE SCHEDULE IS READY
        sampleScheduleForTesting = """EES 02 SCHECHTER HES 04 MCROYMENDELL HLS 01 WEISSMAN HVS 06 TRAINOR MQS 01 BROOKS PES 01 CHOY SQS 01 REEP ZLN 05 GEL LOWE ZQT 01 SPORTS TEAM"""
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
        #for word in wordsList:
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
        #for k in range 
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
            #print wordsList[numIndeces[j]]
            tempList = []
            tempList.append(wordsList[numIndeces[j]-1])
            tempList.append(wordsList[numIndeces[j]])
            #print tempList
            s = ""
            for k in range (numIndeces[j]+1, numIndeces[j-1]-1):
                s = s + wordsList[k] + " "
            tempList.append(s[:-1])
            print tempList
            allClasses.append(tempList)
            print wordsList[numIndeces[j-1]-1]
            #print str(numIndeces[j]) + " " + str(numIndeces[j-1])
            '''for k in range(numIndeces[j], numIndeces[j-1]-1):
                print "k: " + wordsList[k]'''
            #tempList.append(wordsList[numIndeces[k]])
            #tempList.append(s)
            j = j + 1
        db.students.insert({'name':'adduserlater', 'id':1847, 'classes': allClasses})
        print allClasses
        for x in db.students.find():
            print x
        """
        classes = ["EE", "HE", "HL", "HV", "MQ"]
        sections = [ "02", "04", "01", "06", "01" ]
        teachers = ["Schechter", "McroyMendell", "Weissman", "Trainor", "Brooks"]
        db.classes.insert({'student name': 'Blah'})"""
        return str(wordsList)
        #return image_to_string(img)
        #return "HI"


        '''       schedule = request.form.get("txtsched")
        print schedule
        username = request.form.get("username", None)
        friends={}
        classNum = 0
        for line in schedule.split("\n"):
            classNum += 1
            print "beginning of line: " + " ".join(line.split())
            db.classes.insert({"teachername": line.split()[0], "section": line.split()[1], "teacher": line.split()[2], "studentname": username})
###DOESN'T WORK YET, BUT ALMOST-- this finds other people that share your classes
            otherPeople = db.classes.find({"teachername": line.split()[0], "section": line.split()[1], "teacher": line.split()[2]})
            for friend in otherPeople:
                friends[classNum]=friend['studentname']
        for x in db.classes.find():
            print x
        print "FRIENDS LIST: " + str(friends)
        #db.classes.remove()
        return render_template("schedule.html",url2="/",link2="Home",url1="/register",link1="Register")'''



    return render_template("login.html",url2="/",link2="Home",url1="/register",link1="Register")

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
            db.users.insert ( { 'name': username, 'pword': passw, 'n': 0 , 'schedule': 0, 'confirmed': 0} )
            #return "<h1>Thanks for joining!</h1>" + str ( { 'name':username, 'pword': passw } )
            flash("Thanks for joining! Please log in now.")
            return redirect(url_for('login'))
        else:
            flash("Please select an available username")
            #return "<h1>Please select an available username</h1>"
            return redirect(url_for('register'))
    return render_template("register.html",url2="/login",link2="Login",url0="/",link0="Home",url1="/about",link1="About")

@app.route("/confirm/<username>/<schedule>", methods=["GET", "POST"])
def confirm(username, schedule):
    if session['user'] == username:
        db.users.update({'name':username}, {'$set':{'confirmed':1}})
        return redirect(url_for('analyzeSchedule',username=username, schedule=schedule))
    else:
        return "dont enter this url"

@app.route("/analyzeSchedule/<username>/<schedule>", methods=["GET", "POST"])
def analyzeSchedule(username, schedule):
    return render_template("loggedinwithschedule.html", username=username, n=0, url1="/exclusive", link1="Exclusively for Users", url2="/logout", link2="Logout", schedule=schedule)

@app.route("/logout")
def logout():
    print "logout"
    del session['user']
    return redirect(url_for('home'))

@app.route("/enter", methods=["GET", "POST"])
def enter():
    if request.method=="POST":
        return "hi"
    else:
        ###Screenshotting works if you zoom in to make your schedule fit the entire window
        img = Image.open("blah/test.png")
        sampleScheduleForTesting = """EES 02 SCHECHTER HES 04 MCROYMENDELL HLS 01 WEISSMAN HVS 06 TRAINOR MQS 01 BROOKS PES 01 CHOY SQS 01 REEP ZLN 05 GEL LOWE ZQT 01 SPORTS TEAM"""
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
        #for word in wordsList:
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
        #for k in range 
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
            #print wordsList[numIndeces[j]]
            tempList = []
            tempList.append(wordsList[numIndeces[j]-1])
            tempList.append(wordsList[numIndeces[j]])
            #print tempList
            s = ""
            for k in range (numIndeces[j]+1, numIndeces[j-1]-1):
                s = s + wordsList[k] + " "
            tempList.append(s[:-1])
            print tempList
            allClasses.append(tempList)
            print wordsList[numIndeces[j-1]-1]
            #print str(numIndeces[j]) + " " + str(numIndeces[j-1])
            '''for k in range(numIndeces[j], numIndeces[j-1]-1):
                print "k: " + wordsList[k]'''
            #tempList.append(wordsList[numIndeces[k]])
            #tempList.append(s)
            j = j + 1
        db.students.insert({'name':'adduserlater', 'id':1847, 'classes': allClasses})
        print allClasses
        for x in db.students.find():
            print x
        db.students.remove()
        """
        classes = ["EE", "HE", "HL", "HV", "MQ"]
        sections = [ "02", "04", "01", "06", "01" ]
        teachers = ["Schechter", "McroyMendell", "Weissman", "Trainor", "Brooks"]
        db.classes.insert({'student name': 'Blah'})"""
        return str(wordsList)
        #return image_to_string(img)
        #return "HI"

if __name__== "__main__":
    db.users.remove()
    app.debug = True
    app.run(port=5555)
