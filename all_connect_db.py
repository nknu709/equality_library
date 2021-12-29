from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import csv
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

#下面的連結要填 database 的 url
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://petuxltwkykvfr:2a66879a97f1012eafcfcea326bd2692f4c011f05220b36e4c40beea836fb2de@ec2-23-20-205-19.compute-1.amazonaws.com:5432/dccdccgbctfoj5'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


with open('booklist.csv', newline='',encoding = 'utf8') as f:
	#csv_reader = csv.DictReader(f)
	csv_reader = csv.reader(f)
	book_id = []
	book_name = []
	book_publisher = []
	for row in csv_reader:
		book_id.append(row[0])
		book_name.append(row[1])
		book_publisher.append(row[2])

conn = psycopg2.connect(database="dccdccgbctfoj5", user="petuxltwkykvfr", password="2a66879a97f1012eafcfcea326bd2692f4c011f05220b36e4c40beea836fb2de", host="ec2-23-20-205-19.compute-1.amazonaws.com", port="5432")
cur = conn.cursor()
#cur.execute("DROP TABLE booklist")
#conn.commit()

#用井字號起來是因為已經存在--by學妹
#cur.execute('''CREATE TABLE booklist(id SERIAL PRIMARY KEY,book_id TEXT,book_name TEXT,if_borrow TEXT,people_id TEXT,borrow_status TEXT,borrow_class TEXT,people_name TEXT,borrow_time TEXT, publisher TEXT);''')

for i in range(0,len(book_id)):
	book_id_i = book_id[i]
	book_name_i = book_name[i]
	book_publisher_i = book_publisher[i]
	cur.execute("INSERT INTO  booklist (book_id, book_name, publisher) VALUES ('{bookid}', '{bookname}','{publisher}')".format(bookid=book_id_i,bookname=book_name_i, publisher=book_publisher_i))
	conn.commit()

cur.execute("UPDATE booklist SET if_borrow='未借出' WHERE if_borrow IS NULL")
conn.commit()



#cur.execute("DROP TABLE loginlist")
#conn.commit()

#cur.execute('''CREATE TABLE loginlist(id SERIAL PRIMARY KEY, account TEXT, password TEXT, email TEXT, status TEXT);''')
cur.execute("INSERT INTO loginlist (account, password) VALUES ('equality3806384', '{password}')".format(password='manager'))
cur.execute("INSERT INTO loginlist (account, password) VALUES ('551K02', '{password}')".format(password='user'))
conn.commit()

#cur.execute("DROP TABLE history")
#conn.commit()

#cur.execute('''CREATE TABLE history(id SERIAL PRIMARY KEY,borrow_time TEXT,book_id TEXT,book_name TEXT, publisher TEXT,if_borrow TEXT,people_id TEXT,people_status TEXT,people_class TEXT,people_name TEXT);''')
conn.commit()

with open('peoplelist.csv', newline='',encoding = 'utf8') as f:
	#csv_reader = csv.DictReader(f)
	csv_reader = csv.reader(f)
	peo_id = []
	peo_class = []
	peo_sta = []
	#peo_num = []
	peo_name = []
	for row in csv_reader:
		peo_id.append(row[0])
		peo_class.append(row[3])
		peo_sta.append(row[4])
		#peo_num.append(row[3])
		peo_name.append(row[2])

#cur.execute("DROP TABLE peoplelist")
#conn.commit()

#cur.execute('''CREATE TABLE peoplelist(
#	id SERIAL PRIMARY KEY,
#	people_id TEXT,
 #   people_status TEXT,
  #  people_class TEXT,
   # people_name TEXT);''')

for i in range(0,len(peo_id)):
	peo_id_i = peo_id[i]
	peo_class_i = peo_class[i]
	peo_sta_i = peo_sta[i]
	#peo_num_i = peo_num[i]
	peo_name_i = peo_name[i]
	#print(type(book_id_i))
	#print(book_id_i)

	cur.execute("INSERT INTO  peoplelist (people_id, people_class, people_status, people_name) VALUES ('{peoid}', '{peoclass}', '{peosta}', '{peoname}')".format(peoid=peo_id_i,peoclass=peo_class_i,peosta=peo_sta_i,peoname=peo_name_i, ))
	conn.commit()



with open('teachaid_list.csv', newline='',encoding = 'utf8') as f:
	#csv_reader = csv.DictReader(f)
	csv_reader = csv.reader(f)
	teachaid_id = []
	teachaid_name = []
	teachaid_number = []
	for row in csv_reader:
		teachaid_id.append(row[0])
		teachaid_number.append(row[1])
		teachaid_name.append(row[2])


#cur.execute('''CREATE TABLE teachaid_list(id SERIAL PRIMARY KEY,teachaid_id TEXT,teachaid_name TEXT, teachaid_number TEXT,if_borrow TEXT,people_id TEXT,borrow_status TEXT,borrow_class TEXT,people_name TEXT,borrow_time TEXT, teachaid_image TEXT);''')

#bytea


for i in range(0,len(teachaid_id)):
	aid_id_i = teachaid_id[i]
	aid_name_i = teachaid_name[i]
	aid_num_i = teachaid_number[i]
	print(aid_id_i)

	cur.execute('''INSERT INTO  teachaid_list (teachaid_id, teachaid_name, teachaid_number) VALUES ('{aid_id}', '{aid_name}', '{aid_num}')'''.format(aid_id=aid_id_i,aid_name=aid_name_i,aid_num=aid_num_i, ))
	conn.commit()

cur.execute("UPDATE teachaid_list SET if_borrow='未借出' WHERE if_borrow IS NULL")
conn.commit()

#do we need teaching_history?

#cur.execute('''CREATE TABLE teachaid_his(id SERIAL PRIMARY KEY,borrow_time TEXT,teachaid_id TEXT,teachaid_name TEXT, teachaid_number TEXT,if_borrow TEXT,people_id TEXT,people_status TEXT,people_class TEXT,people_name TEXT);''')
conn.commit()

cur.close()
conn.close()

#if __name__ == '__main__':
#    manager.run()

