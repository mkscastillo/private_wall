from flask import Flask, render_template, request, redirect, session, flash, jsonify
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'secretkeys'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 
bcrypt =Bcrypt(app)

@app.route('/', methods=['POST','GET'])
def index():
    return render_template("index.html")

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    session['isLoggedIn']=False
    flash("You have been logged out","loggedout")
    return render_template("index.html")

@app.route('/create' , methods=['POST','GET'])
def create():
    if len(request.form['fname'])<2:
        flash("This is a required field","fname")
    if not all(x.isalpha() or x.isspace() for x in request.form['fname']): 
        flash("Make sure your first name only has letters in it","fname")
    if len(request.form['lname'])<2:
        flash("This is a required field","lname")
    if not all(x.isalpha() or x.isspace() for x in request.form['lname']): 
        flash("Make sure your last name only has letters in it","lname")
    if len(request.form['email'])<2:
        flash("This is a required field","email")
    else:
        if not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
            flash("Invalid email address!","email")
    if len(request.form['pword'])>=8 and len(request.form['pwordconf'])>=8 and len(request.form['pword'])<=15 and len(request.form['pwordconf'])<=15:
        if request.form['pword'] == request.form['pwordconf']:
            if re.search('[0-9]',request.form['pword']) is None:
                flash("Password must contain a number, a capital letter, and be between 8-15 characters","pword")
            if re.search('[A-Z]',request.form['pword']) is None: 
                flash("Password must contain a number, a capital letter, and be between 8-15 characters","pword")
        else:
            flash("Passwords must match","pwordconf")
    else:
        flash("Password must contain a number, a capital letter, and be between 8-15 characters","pword")

    if not '_flashes' in session.keys():
        mysql = connectToMySQL('users')
        query = "SELECT email FROM login WHERE email = %(e)s;"
        data = {
            "e": request.form['email'],
        }
        email = mysql.query_db(query, data)
        if email:
            flash("Email is taken","email")
        else:
            pw_hash = bcrypt.generate_password_hash(request.form['pword'])
            mysql = connectToMySQL('users')
            query = "INSERT INTO login (fname,lname, email, password) VALUES (%(f)s, %(n)s, %(e)s,%(p)s);"
            data = {
                "f": request.form["fname"],
                "n": request.form["lname"],
                "e": request.form["email"],
                "p": pw_hash,
            }
            session['id'] = mysql.query_db(query, data)
            session['name']=request.form["fname"]
            session['isLoggedIn']=True
            flash("You have been successfully registered","register")
            return redirect('/success')
    return render_template("index.html",fname=request.form['fname'],lname=request.form['lname'],email=request.form['email'])

@app.route('/login' , methods=['POST','GET'])
def login():
    mysql = connectToMySQL('users')
    query = "SELECT * FROM login WHERE email = %(e)s;"
    data = {
        "e": request.form['loginemail']
    }
    login = mysql.query_db(query, data)
    if login:
        if bcrypt.check_password_hash(login[0]['password'], request.form['loginpword']):
            session['id'] = login[0]['id']
            session['name']=login[0]['fname']
            session['isLoggedIn']=True
            return redirect('/success')
    flash("You could not be logged in","login")
    return render_template("index.html",loginemail=request.form['loginemail'])

@app.route("/success")
def success():
    print("-"*30,"page is reloaded")
    if session['isLoggedIn']:
        mysql = connectToMySQL('users')
        query = "SELECT login.fname as name_from,messages.message as message, messages.created_at as created_at,messages.id as id FROM messages JOIN login ON login.id = messages.friend_id WHERE user_id = %(id)s;"
        data = {
            "id": session['id'],
        }
        messages = mysql.query_db(query, data)

        mysql = connectToMySQL('users')
        query = "SELECT * FROM login WHERE id!=%(id)s;"
        data = {
            "id": session['id'] }
        friends = mysql.query_db(query,data)
        return render_template('login.html',id=session['id'],name=session['name'],isLoggedIn=session['isLoggedIn'],messages=messages,friends=friends)
    return redirect('/')

@app.route("/delete", methods=['GET','POST'])
def delete():
    print("*"*30,"inside delete")
    mysql = connectToMySQL('users')
    query = "DELETE FROM messages WHERE id = %(id)s;"
    data = {
        # "id": request.args.get('id')
        "id": request.form['id']
    }
    result = mysql.query_db(query, data)
    print("*"*30,result)

    if result:
        # return redirect('/success')
        # return jsonify({'msg':'success','id':request.args.get('id')})
        return render_template('partials/blank.html')

@app.route("/post", methods=['GET','POST'])
def post():
    print("*"*30,"inside post")
    mysql = connectToMySQL('users')
    query = "INSERT INTO messages (user_id,friend_id,message) VALUES (%(uid)s, %(fid)s, %(mess)s);"
    data = {
        "uid": request.form['friend_id'],
        "fid": session['id'],
        "mess": request.form['comment']
    }
    # if len(request.args.get('comment'))<5:
    #     flash("Message should be longer than 5 characters","sent")
    #     return redirect('/success')
    mysql.query_db(query, data)
    print("*"*30,"almost rendering")
    return render_template('partials/blank.html')
    # return redirect('/success')

if __name__ == "__main__":
    app.run(debug=True)