CREATE DATABASE IF NOT EXISTS photo_share;
USE photo_share;

CREATE TABLE User
(user_id INTEGER,
first_name CHAR(20) NOT NULL,
last_name CHAR(20) NOT NULL,
email CHAR(20) NOT NULL UNIQUE,
dob DATE NOT NULL,
gender CHAR(20),
hometown CHAR(20),
password CHAR(20) NOT NULL,
PRIMARY KEY (user_id));

CREATE TABLE Friends
(friend1_id INTEGER NOT NULL,
friend2_id INTEGER NOT NULL,
PRIMARY KEY (friend1_id, friend2_id),
FOREIGN KEY (friend1_id) REFERENCES User(user_id) ON DELETE CASCADE,
FOREIGN KEY (friend2_id) REFERENCES User(user_id) ON DELETE CASCADE,
CHECK (friend1_id <> friend2_id));

CREATE TABLE Album
(album_id INTEGER,
album_name CHAR(20) NOT NULL,
creation_datetime DATETIME NOT NULL,
owner_id INTEGER NOT NULL,
FOREIGN KEY (owner_id) REFERENCES User(user_id) ON DELETE CASCADE, 
PRIMARY KEY (album_id));

CREATE TABLE Photo
(photo_id INTEGER,
photo_data LONGBLOB NOT NULL,
caption CHAR(100),
album_id INTEGER NOT NULL,
upload_datetime DATETIME NOT NULL,
FOREIGN KEY (album_id) REFERENCES Album(album_id) ON DELETE CASCADE, 
PRIMARY KEY (photo_id));

CREATE TABLE Photo_comment
(comment_id INTEGER,
comment_text CHAR(100) NOT NULL,
comment_datetime DATETIME NOT NULL,
owner_id INTEGER NOT NULL,
photo_id INTEGER NOT NULL,
FOREIGN KEY (owner_id) REFERENCES User(user_id) ON DELETE CASCADE, 
FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE, 
PRIMARY KEY (comment_id));


CREATE TABLE Photo_like
(like_id INTEGER,
owner_id INTEGER NOT NULL,
photo_id INTEGER NOT NULL,
FOREIGN KEY (owner_id) REFERENCES User(user_id) ON DELETE CASCADE, 
FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE, 
PRIMARY KEY (like_id));

CREATE TABLE Tag
(tag_name CHAR(20) NOT NULL,
photo_id INTEGER NOT NULL,
FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE,
PRIMARY KEY (tag_name, photo_id));

