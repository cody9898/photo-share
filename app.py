######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from werkzeug.wrappers import CommonRequestDescriptorsMixin
from flaskext.mysql import MySQL
import flask_login
import yaml
from datetime import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

creds = yaml.safe_load(open("creds.yaml", "r"))

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = creds["MYSQL_DATABASE_PASSWORD"]
app.config['MYSQL_DATABASE_DB'] = 'photo_share'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
# cursor = conn.cursor()
# cursor.execute("SELECT email from User")
# users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email, user_id from User")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	# Get list of all user_id in db
	users = getUserList()
	for tup in users:
		if tup[0] == email:
			user = User()
			user.id = tup[1]
			return user
	return
	

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	for tup in users:
		if tup[0] == email:
			user = User()
			user.id = tup[1]
			cursor = mysql.connect().cursor()
			cursor.execute("SELECT password FROM User WHERE email = '{0}'".format(email))
			data = cursor.fetchall()
			pwd = str(data[0][0] )
			user.is_authenticated = request.form['password'] == pwd
			return user
	return



# functions
def fetchData(cursor):
	data = []
	for item in cursor:
		data.append(item)
	return data


def getNextId(entity,idcol):
	try:
		cursor = conn.cursor()
		query = "select MAX(x."+idcol+") from "+entity+" x;"
		cursor.execute(query)
		queryData = fetchData(cursor)
		cursor.close()
		nextId = queryData[0][0] + 1
		return nextId
	except Exception as e:
		return 0


def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photo p, Album a WHERE p.album_id = a.album_id AND a.owner_id = '{0}' ORDER BY upload_datetime DESC".format(uid))
	return cursor.fetchall()


def getAlbumPhotos(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photo WHERE album_id = '{}' ORDER BY upload_datetime DESC".format(album_id))
	return cursor.fetchall()


def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photo ORDER BY upload_datetime DESC")
	return cursor.fetchall()


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM User WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]


def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM User WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True


def getLikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT like_id, owner_id, first_name, last_name FROM Photo_like l, User u WHERE u.user_id = l.owner_id AND photo_id = '{0}' ".format(photo_id))
	data = fetchData(cursor)
	cursor.close()
	return data


def checkIfLiked(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT like_id, owner_id FROM Photo_like WHERE photo_id = '{0}' ".format(photo_id))
	likes = fetchData(cursor)
	cursor.close()
	if flask_login.current_user.is_authenticated:
		for like in likes:
			if like[1] == flask_login.current_user.id:
				return True
	return False


def getPhotoDetails(photo_id):
	photoDetails = {}

	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption, owner_id, p.album_id, a.album_name FROM Photo p, Album a WHERE p.photo_id = '{0}' AND p.album_id = a.album_id".format(photo_id))
	data = fetchData(cursor)
	cursor.close()

	user = getUserDetails(data[0][3])
	photoDetails['first_name'], photoDetails['last_name'] = user['first_name'], user['last_name']
	
	photoDetails['owner_id'] = data[0][3]
	photoDetails['photo_data'] = data[0][0]
	photoDetails['caption'] = data[0][2]
	photoDetails['album_id'] = data[0][4]
	photoDetails['photo_id'] = data[0][1]
	photoDetails['album_name'] = data[0][5]

	photoDetails['likes'] = getLikes(photo_id)
	photoDetails['num_likes'] = len(photoDetails['likes'])

	return photoDetails


def getUserDetails(user_id):
	userDetails = {}

	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name FROM User WHERE user_id = '{0}' ".format(user_id))
	data = fetchData(cursor)
	cursor.close()
	userDetails['first_name'] = data[0][0]
	userDetails['last_name'] = data[0][1]
	return userDetails


def getAlbums(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, album_name FROM Album WHERE owner_id = '{0}' ORDER BY creation_datetime DESC".format(user_id))
	data = fetchData(cursor)
	cursor.close()
	return data


def amIuser(user_id):
	authenticated = flask_login.current_user.is_authenticated
	if authenticated:
		if int(user_id) == int(flask_login.current_user.id):
			return True
		else:
			return False



def getTags(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT tag_name FROM tag WHERE photo_id = {0}".format(photo_id))
	data = fetchData(cursor)
	return data


def getFirstName():
	cursor = conn.cursor()
	cursor.execute("SELECT first_name FROM User WHERE user_id = '{0}'".format(flask_login.current_user.id))
	first_name = fetchData(cursor)[0][0]
	cursor.close()
	return first_name


def getFriends(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT friend1_id, first_name, last_name FROM friends f, user u WHERE u.user_id = f.friend1_id AND f.friend2_id = {0}".format(user_id))
	data1 = fetchData(cursor)
	cursor.close()

	cursor = conn.cursor()
	cursor.execute("SELECT friend2_id, first_name, last_name FROM friends f, user u WHERE u.user_id = f.friend2_id AND friend1_id = {0}".format(user_id))
	data2 = fetchData(cursor)
	cursor.close()
	return data1 + data2


def checkIfFriend(user_id):
	me = flask_login.current_user.id
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM friends WHERE (friend1_id = {0} AND friend2_id ={1}) OR (friend1_id = {2} AND friend2_id = {3})".format(me,user_id,user_id,me))
	data = fetchData(cursor)
	cursor.close()
	if len(data) > 0:
		return True
	else:
		return False

	
def getScore(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(photo_id) FROM photo p, album a WHERE p.album_id = a.album_id AND a.owner_id = {0}".format(user_id))
	countPhotos = fetchData(cursor)
	cursor.close()

	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(comment_id) FROM photo p, album a, photo_comment c WHERE p.album_id = a.album_id AND p.photo_id = c.photo_id AND c.owner_id = {0} AND a.owner_id <> {1}".format(user_id, user_id))
	countComments = fetchData(cursor)
	cursor.close()

	return countPhotos[0][0] + countComments[0][0]


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM User WHERE email = '{0}'".format(email)):
		data = fetchData(cursor)
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect('/profile') #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('browse.html', loggedIn=False, message='Logged out', photos=getAllPhotos(), base64=base64)


@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')


#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
	try:
		email = request.form.get('email')
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		dob = request.form.get('dob')
		gender = request.form.get('gender')
		hometown = request.form.get('hometown')
		password = request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect('/register')
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		user_id = getNextId("User","user_id")
		insertStr = '''INSERT INTO User (user_id, first_name, last_name, email, dob, gender, hometown, password)
			VALUES ({0}, '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}');'''
		print(cursor.execute(insertStr.format(user_id,first_name,last_name,email,dob,gender,hometown,password)))
		conn.commit()
		cursor.close()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('browse.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect('/register')

#end login code


@app.route('/profile')
@flask_login.login_required
def protected():
	first_name = getFirstName()
	return render_template('profile.html', name=first_name, score=getScore(flask_login.current_user.id), user_id=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(flask_login.current_user.id),base64=base64)


#begin photo uploading code
@app.route('/select_album', methods=['GET'])
def selectAlbum():
	albums = getAlbums(flask_login.current_user.id)
	if len(albums) == 0:
		return render_template('create_album.html', message="You must create an album before uploading a photo")
	else:
		return render_template('select_album.html', albums=albums)


# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload/<album_id>', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(album_id):
	if request.method == 'POST':
		photo_id = getNextId("Photo","photo_id")
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		tags = request.form.get('tags').split(",")
		photo_data =imgfile.read()
		upload_datetime = str(datetime.now())
		try:
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Photo (photo_id, photo_data, caption, album_id, upload_datetime) VALUES (%s, %s, %s, %s, %s)''' ,(photo_id, photo_data, caption, album_id, upload_datetime))
			conn.commit()
			cursor.close()
			for tag in tags:
				print(tag)
				cursor = conn.cursor()
				cursor.execute("INSERT INTO Tag(tag_name, photo_id) VALUES ('{0}', {1})".format(tag, photo_id))
				conn.commit()
				cursor.close()
		except Exception as e:
			print(e)
		return redirect('/profile')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		cursor = conn.cursor()
		cursor.execute("SELECT album_id, album_name FROM Album WHERE album_id = '{0}'".format(album_id))
		data = fetchData(cursor)
		cursor.close()
		return render_template('upload.html', album=data[0])
#end photo uploading code


@app.route('/photo/<photo_id>', methods=['GET'])
def photo(photo_id):
	# get all details about photo
	photoDetails = getPhotoDetails(photo_id)
	auth = flask_login.current_user.is_authenticated
	return render_template('photo.html', auth=auth, canDelete=amIuser(photoDetails['owner_id']), album_id=photoDetails['album_id'], liked=checkIfLiked(photo_id), photo=photoDetails, owner=photoDetails['owner_id'], tags=getTags(photo_id), photo_id=photo_id, data=photoDetails['photo_data'], base64=base64)


@app.route('/delete_photo/<photo_id>', methods=['GET'])
def deletePhoto(photo_id):
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM Photo WHERE photo_id = {0}'''.format(photo_id))
		conn.commit()
		cursor.close()
		return render_template('browse.html', loggedIn=flask_login.current_user.is_authenticated, message='Photo deleted', photos=getAllPhotos(), base64=base64)
	except Exception as e:
		print(e)
		photoDetails = getPhotoDetails(photo_id)
		return render_template('photo.html', message="Error deleting photo", album_id=photoDetails['album_id'], liked=checkIfLiked(photo_id), photo=photoDetails, owner=photoDetails['owner_id'], photo_id=photoDetails['photo_id'], data=photoDetails['photo_data'], base64=base64)


@app.route('/delete_album/<album_id>', methods=['GET'])
def deleteAlbum(album_id):
	try:
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM Album WHERE album_id = {0}'''.format(album_id))
		conn.commit()
		cursor.close()
		return render_template('browse.html', loggedIn=flask_login.current_user.is_authenticated, message='Album deleted', photos=getAllPhotos(), base64=base64)
	except Exception as e:
		print(e)
		# get owner name and photos in album
		cursor = conn.cursor()
		cursor.execute("SELECT album_name, owner_id FROM Album WHERE album_id = '{0}'".format(album_id))
		album = fetchData(cursor)[0]
		cursor.close()
		owner = getUserDetails(album[1])
		photos = getAlbumPhotos(id)

		return render_template('album.html', message="Error deleting album", canDelete=amIuser(album[1]), photos=photos, owner=owner, owner_id=album[1], album_name=album[0], base64=base64)


# perform the action of liking a photo
@app.route('/like/<photo_id>', methods=['GET'])
@flask_login.login_required
def likePhoto(photo_id):
	owner_id = flask_login.current_user.id
	like_id = getNextId('Photo_like', 'like_id')
	cursor = conn.cursor()
	cursor.execute('''INSERT INTO Photo_like (like_id, owner_id, photo_id) VALUES (%s, %s, %s)''' ,(like_id, owner_id, photo_id))
	conn.commit()
	cursor.close()
	return flask.redirect(url_for('photo', photo_id=photo_id))


# perform the action of unliking a photo
@app.route('/unlike/<photo_id>', methods=['GET'])
@flask_login.login_required
def unlikePhoto(photo_id):
	owner_id = flask_login.current_user.id
	cursor = conn.cursor()
	cursor.execute('''DELETE FROM Photo_like WHERE owner_id = %s AND photo_id = %s''' ,(owner_id, photo_id))
	conn.commit()
	cursor.close()
	return flask.redirect(url_for('photo', photo_id=photo_id))


# show list of people who liked it
@app.route('/likes/<photo_id>', methods=['GET'])
def showLikes(photo_id):
	likes = getLikes(photo_id)
	return render_template('likes.html', photo_id=photo_id, likes=likes)


# show list of comments
@app.route('/comments/<photo_id>', methods=['GET', 'POST'])
def showComments(photo_id):
	showError = False
	if flask_login.current_user.is_authenticated:
		# check if this is my photo
		cursor = conn.cursor()
		cursor.execute("SELECT owner_id FROM photo p, album a WHERE p.album_id = a.album_id AND p.photo_id = {0}".format(photo_id))
		data = fetchData(cursor)
		cursor.close()
		owner = data[0][0]
		current_user = flask_login.current_user.id
		if owner == current_user:
			auth = False
		else:
			auth = True
	else:
		auth = False
		current_user = -1

	if request.method == 'POST':
		# post comment and show updated list
		comment_text = request.form.get('comment_text')
		query = request.form.get('query')

		if comment_text is not None:
			owner_id = flask_login.current_user.id
			comment_datetime = datetime.now()
			comment_id = getNextId("Photo_comment", "comment_id")
			try:
				cursor = conn.cursor()
				cursor.execute('''INSERT INTO Photo_comment (comment_id, comment_text, comment_datetime, owner_id, photo_id) VALUES (%s, %s, %s, %s, %s)''' ,(comment_id, comment_text, comment_datetime, owner_id, photo_id))
				conn.commit()
				cursor.close()
			except Exception as e:
				print(e)
				showError = True
		else:
			# search comments
			cursor = conn.cursor()
			cursor.execute("SELECT comment_id, comment_text, owner_id, first_name, last_name FROM Photo_comment c, User u WHERE c.owner_id = u.user_id AND c.photo_id = '{0}' AND c.comment_text = '{1}' ORDER BY comment_datetime DESC".format(photo_id, query))
			data = fetchData(cursor)
			cursor.close()

			if len(data) == 0:
				return render_template('comments.html', comments=data, auth=auth, photo_id=photo_id, current_user=current_user, message="No comments match your search")
			else:
				return render_template('comments.html', comments=data, auth=auth, photo_id=photo_id, current_user=current_user)

	# show list of comments
	cursor = conn.cursor()
	cursor.execute("SELECT comment_id, comment_text, owner_id, first_name, last_name FROM Photo_comment c, User u WHERE c.owner_id = u.user_id AND c.photo_id = '{0}' ORDER BY comment_datetime DESC".format(photo_id))
	data = fetchData(cursor)
	cursor.close()

	if showError:
		return render_template('comments.html', comments=data, auth=auth, photo_id=photo_id, current_user=current_user, message="Error posting comment")
	else:
		return render_template('comments.html', comments=data, auth=auth, photo_id=photo_id, current_user=current_user)


@app.route('/delete_comment/<comment_id>', methods=['GET'])
def deleteComment(comment_id):
	# find photo_id so we can redirect after deletion
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Photo_comment WHERE comment_id = {0} ".format(comment_id))
	data = fetchData(cursor)
	cursor.close()
	
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Photo_comment WHERE comment_id = {0} ".format(comment_id))
	conn.commit()
	cursor.close()
	return redirect(url_for('showComments', photo_id=data[0][0]))


@app.route('/tag_all/<tag_name>', methods=['GET'])
def tagAll(tag_name):
	# get all photos with this tag
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, p.photo_id, caption FROM Tag t, Photo p WHERE t.tag_name = '{0}' AND t.photo_id = p.photo_id ORDER BY p.upload_datetime DESC".format(tag_name))
	photos = fetchData(cursor)
	cursor.close()
	return render_template('tag.html', showAll=True, photos=photos, tag_name=tag_name, base64=base64)


@app.route('/tag_mine/<tag_name>', methods=['GET'])
def tagMine(tag_name):
	cursor = conn.cursor()
	user_id = flask_login.current_user.id
	cursor.execute("SELECT photo_data, p.photo_id, caption FROM Tag t, Photo p, Album a WHERE a.album_id = p.album_id AND t.tag_name = '{0}' AND t.photo_id = p.photo_id AND a.owner_id = {1} ORDER BY p.upload_datetime DESC".format(tag_name, user_id))
	photos = fetchData(cursor)
	cursor.close()
	return render_template('tag.html', showAll=False, photos=photos, tag_name=tag_name, base64=base64)


@app.route('/user/<user_id>', methods=['GET'])
def userProfile(user_id):
	authenticated = flask_login.current_user.is_authenticated
	if authenticated:
		isFriend = checkIfFriend(user_id)
		if int(user_id) == int(flask_login.current_user.id):
			return redirect('/profile')
	else:
		isFriend = False
	
	# at this point user_id is a different user
	photos = getUsersPhotos(user_id)
	user = getUserDetails(user_id)
	return render_template('user.html', authenticated=authenticated, score=getScore(user_id), isFriend=isFriend, user_id=user_id, user=user, photos=photos, base64=base64)


@app.route('/create_album', methods=['GET', 'POST'])
@flask_login.login_required
def createAlbum():
	if request.method == 'POST':
		album_name = request.form['album_name']
		creation_datetime = str(datetime.now())
		owner_id = flask_login.current_user.id

		# create new album in db
		try:
			album_id = getNextId("Album", "album_id")
			cursor = conn.cursor()
			tup = (str(album_id), album_name, creation_datetime, str(owner_id))
			cursor.execute('''INSERT INTO Album (album_id, album_name, creation_datetime, owner_id) VALUES (%s, %s, %s, %s)''' ,tup)
			cursor.close()
			conn.commit()
			return redirect(url_for('album', id=album_id))
		except Exception as e:
			print("error inserting album in db:",e)
			return render_template('create_album.html', message="Failed to create album")
	else:
		return render_template('create_album.html')


@app.route('/album/<id>', methods=['GET'])
def album(id):
	# get owner name and photos in album
	cursor = conn.cursor()
	cursor.execute("SELECT album_name, owner_id, album_id FROM Album WHERE album_id = '{0}'".format(id))
	album = fetchData(cursor)[0]
	owner = getUserDetails(album[1])
	photos = getAlbumPhotos(id)
	cursor.close()

	return render_template('album.html', canDelete=amIuser(album[1]), album=album, photos=photos, owner=owner, base64=base64)


@app.route('/user_albums/<user_id>', methods=['GET'])
def userAlbums(user_id):
	albums = getAlbums(user_id)
	if len(albums) == 0:
		empty = True
	else:
		empty = False
	owner = getUserDetails(user_id)
	return render_template('album_list.html', owner=owner, albums=albums, empty=empty)


@app.route('/friends/<user_id>', methods=['GET'])
def friends(user_id):
	friends = getFriends(user_id)
	if len(friends) == 0:
		empty = True
	else:
		empty = False
	owner = getUserDetails(user_id)
	return render_template('friends_list.html', owner=owner, friends=friends, empty=empty)


@app.route('/add_friend/<user_id>', methods=['GET'])
def addFriend(user_id):
	if checkIfFriend(user_id):
		return redirect(url_for('userProfile', user_id=user_id))
	else:
		try:
			me = flask_login.current_user.id
			cursor = conn.cursor()
			cursor.execute('INSERT INTO friends (friend1_id, friend2_id) VALUES ({0},{1})'.format(me,user_id))
			cursor.close()
			conn.commit()
			return redirect(url_for('userProfile', user_id=user_id))
		except Exception as e:
			print(e)
			return redirect(url_for('userProfile', user_id=user_id))


@app.route('/remove_friend/<user_id>', methods=['GET'])
def removeFriend(user_id):
	try:
		me = flask_login.current_user.id
		cursor = conn.cursor()
		cursor.execute('DELETE FROM friends WHERE (friend1_id = {0} AND friend2_id ={1}) OR (friend1_id = {2} AND friend2_id = {3})'.format(me,user_id,user_id,me))
		cursor.close()
		conn.commit()
		return redirect(url_for('userProfile', user_id=user_id))
	except Exception as e:
		print(e)
		return redirect(url_for('userProfile', user_id=user_id))


@app.route('/photo_search', methods=['GET', 'POST'])
def photoSearch():
	if request.method == 'POST':
		query = request.form.get('query')
		cursor = conn.cursor()
		cursor.execute("SELECT photo_data, p.photo_id, caption FROM photo p, tag t WHERE t.photo_id = p.photo_id AND t.tag_name = '{0}' ORDER BY upload_datetime DESC".format(query))
		photos = fetchData(cursor)
		cursor.close()

		if len(photos) > 0:
			message = 'Photos with tag "' + query + '":'
			return render_template('/photo_search.html', photos=photos, message=message, base64=base64)
		else:
			message = "No photos found."
			return render_template('/photo_search.html', message=message)
	else:
		return render_template('photo_search.html')


@app.route('/user_search', methods=['GET', 'POST'])
def userSearch():
	if request.method == 'POST':
		query = request.form.get('query')
		name = query.split(" ")
		cursor = conn.cursor()
		cursor.execute("SELECT user_id, first_name, last_name FROM user WHERE first_name = '{0}' AND last_name = '{1}'".format(name[0], name[1]))
		users = fetchData(cursor)
		cursor.close()

		if len(users) > 0:
			return render_template('/user_search.html', users=users, base64=base64)
		else:
			message = "No users found."
			return render_template('/user_search.html', message=message)
	else:
		return render_template('user_search.html')


@app.route('/top10', methods=['GET'])
def top10():
	# get all user_ids
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, first_name, last_name FROM user")
	userLst = fetchData(cursor)
	cursor.close()

	# get score for each user
	scores = {}
	for user in userLst:
		scores[(user[0], user[1], user[2])] = getScore(user[0])

	# sort the scores
	scoresSorted = sorted(scores.items(), key = lambda keyval : (keyval[1], keyval[0]), reverse = True)
	top10 = scoresSorted[:10]
	return render_template('top10.html', top10=top10)


@app.route('/friend_recommendations', methods=['GET'])
def friendRecommendations():
	me = flask_login.current_user.id
	myFriends = getFriends(me)

	fof = []
	for friend in myFriends:
		f = getFriends(friend[0])
		for user in f:
			if user[0] != me and user not in myFriends:
				fof.append(user)

	if len(fof) == 0:
		return render_template('friend_recommendations.html', fof=[], empty=True)

	fofDict = {}

	for user in fof:
		try:
			# have seen this user already
			fofDict[(user[0], user[1], user[2])] += 1
		except:
			# have not seen this user already
			fofDict[(user[0], user[1], user[2])] = 1
	
	fofSorted = sorted(fofDict.items(), key = lambda keyval : (keyval[1], keyval[0]), reverse = True)

	print(fofSorted)

	return render_template('friend_recommendations.html', fof=fofSorted[:10], empty=False)


@app.route('/photo_recommendations', methods=['GET'])
def photoRecommendations():
	me = flask_login.current_user.id
	myPhotos = getUsersPhotos(me)

	tags = []

	for photo in myPhotos:
		t = getTags(photo[1])
		for tag in t:
			tags.append(tag)

	tagsDict = {}

	for t in tags:
		try: 
			tagsDict[t[0]] += 1
		except:
			tagsDict[t[0]] = 1

	tagsSorted = sorted(tagsDict.items(), key = lambda keyval : (keyval[1], keyval[0]), reverse = True)
	top5 = tagsSorted[:5]

	ranking = {}
	ranking[1] = {}
	ranking[2] = {}
	ranking[3] = {}
	ranking[4] = {}
	ranking[5] = {}

	# get all photos that are not mine
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photo p, Album a WHERE p.album_id = a.album_id AND a.owner_id <> '{0}'".format(me))
	photos = fetchData(cursor)
	cursor.close()

	for photo in photos:
		temp = getTags(photo[1])
		photoTags = []
		for t in temp:
			photoTags.append(t[0])
		rank = 0
		for t in top5:
			if t[0] in photoTags:
				rank += 1
		
		if rank > 0:
			ranking[rank][photo] = len(photoTags)

	finalLst = []

	for i in range(1,6):
		if len(ranking[i]) > 0:
			rankedRanking = sorted(ranking[i].items(), key = lambda keyval : (keyval[1], keyval[0]), reverse = True)
			for photo in rankedRanking:
				finalLst.append(photo[0])

	finalLst.reverse()

	if len(finalLst) == 0:
		empty = True
	else:
		empty = False

	return render_template('photo_recommendations.html', photos=finalLst, empty=empty, base64=base64)


@app.route('/pop_tags', methods=['GET'])
def popTags():
	cursor = conn.cursor()
	cursor.execute('SELECT tag_name, COUNT(tag_name) FROM tag GROUP BY tag_name ORDER BY COUNT(tag_name) DESC ')
	tags = fetchData(cursor)
	return render_template('pop_tags.html', tags=tags)

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('browse.html', loggedIn=flask_login.current_user.is_authenticated, message='Welcome to Photoshare', photos=getAllPhotos(), base64=base64)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
