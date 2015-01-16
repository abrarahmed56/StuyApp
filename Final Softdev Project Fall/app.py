from flask import Flask, request, redirect, url_for, render_template, flash, session
from pymongo import Connection
from pytesser import *
from PIL import Image
import json, urllib2
import os
import base64

app = Flask(__name__)
app.secret_key = "secret"
conn = Connection()
db = conn ['stuyapp']

@app.route("/")
def home(): 
    return render_template("home.html",url1="/login",link1="Login",url2="/register",link2="Register",url0="/about",link0="About")

@app.route("/login",methods=["GET","POST"])
def login():
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
        if db.users.find_one ( { 'name' : username , 'pword' : passw } ) != None:
            #flash("correct login info")
            n = db.users.update ( { 'name': username } , { '$inc': { 'n' : 1 } } )
	    #for q in db.users.find({'name':username}):
 	        #print int(str(q)[str(q).find("u'n': ")+6: str(q).rfind("}")])
	    q = db.users.find({'name':username})[0]
	    n = int(str(q)[str(q).find("u'n': ")+6: str(q).rfind("}")])
            #n = n + 1
            #session['n']=n
	    for x in db.users.find({'name': username,'pword':passw}):
	        print "bleh" + str(db.users.find({'name':username,'pword':passw}))
            session['user']=username
            return render_template("loggedin.html", username=username, n=n,url1="/exclusive",link1="Exclusively for Users",url2="/logout",link2="Logout")
        else: 
            flash("incorrect login info")
            return redirect(url_for('login'))
    elif request.method=="POST" and request.form.get("h")=="bleh":
        schedule = request.form.get("txtsched")
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
        return render_template("schedule.html",url2="/",link2="Home",url1="/register",link1="Register")
    return render_template("login.html",url2="/",link2="Home",url1="/register",link1="Register")

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
            db.users.insert ( { 'name': username, 'pword': passw, 'n': 0 } )
            #return "<h1>Thanks for joining!</h1>" + str ( { 'name':username, 'pword': passw } )
            flash("Thanks for joining! Please log in now.")
            return redirect(url_for('login'))
        else:
            flash("Please select an available username")
            #return "<h1>Please select an available username</h1>"
            return redirect(url_for('register'))
    return render_template("register.html",url2="/login",link2="Login",url0="/",link0="Home",url1="/about",link1="About")

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
    app.debug = True
    app.run(port=5555)
