from flask import render_template, flash, redirect,session, request, url_for
from flask_wtf import FlaskForm
import csv
import psycopg2
from wtforms import StringField, SelectField, PasswordField, RadioField
import time
import datetime
from flask_mail import Mail, Message
import os
import smtplib 
from werkzeug.security import generate_password_hash, check_password_hash
import copy
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired, BadSignature
from wtforms.validators import DataRequired, Email
from flask import Flask, g, current_app
#from PIL import Image
#from skimage import transform
#import matplotlib.pyplot as plt


app = Flask(__name__)
app.config['SECRET_KEY']='my-son-slowlyslowly'


from flask import Flask
#from flask_uploads import UploadSet, configure_uploads, IMAGES
#photos = UploadSet('photos', IMAGES)
#configure_uploads(app, photos)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://lqtsgjafkliepk:49e24531007157bf0444f07a0c44a60b1df33909a1bb0e87c92f999be6ec84c6@ec2-54-204-45-43.compute-1.amazonaws.com:5432/de85uk970imaqa'

cur_PATH = 'booklist.db'
BOOK_CSV_PATH = 'booklist.csv'
BOOK_SQL_NAME = 'booklist'

PEOPLE_DB_PATH = 'peoplelist.db'
PEOPLE_CSV_PATH = 'peoplelist_include_status.csv'
PEOPLE_SQL_NAME = 'peoplelist'

Manager_DB_PATH = 'loginlist.db'
Manager_SQL_NAME = 'login'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # 邮件服务器地址
app.config['MAIL_PORT'] = 587               # 邮件服务器端口
app.config['MAIL_USE_TLS'] = True   
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or 'equality.nknu@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or 'nknu@709'

mail = Mail(app)

#-----------------------------------------------------------------------------------
#Home

@app.route('/')
def library():
	return render_template('homebase.html')


#------------------------------------------------------------------------------------
#Login (Manager & User)

class LoginForm(FlaskForm):
	account = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})
	#password = StringField('密碼',validators=[DataRequired()])
	password = PasswordField('',validators=[DataRequired()])


@app.route('/login', methods = ['GET', 'POST'])
def login():
	form = LoginForm()
	return render_template('login.html', form=form)

@app.route('/login/success/<account>/<password>')
def login_successed(account, password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			return render_template('manager_home.html',account=account,password=password)

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			return render_template('user_home.html', account=account, password=password)
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)

	conn.close()

@app.route('/login/solution', methods=['POST'])
def login_solution():

	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	account_input = request.form.get('account')
	password_input = request.form.get('password')

	cur.execute("SELECT account, password, status FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password, status FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = generate_password_hash(manager_detail[1])

	user_account = user_detail[0]
	user_password = generate_password_hash(user_detail[1])

	if (account_input==manager_account):
		check_manager = check_password_hash(manager_password,password_input)
		if (check_manager==1):
			go_to_manager_home = url_for('login_successed', account=account_input, password=manager_password)
			return redirect(go_to_manager_home)

		else:
			error = "帳號或密碼輸入錯誤"
			form = LoginForm()
			#print(manager_detail)
			return render_template('login.html',form=form, error=error)

	elif (account_input==user_account):
		if(check_password_hash(user_password, password_input)==1):
			go_to_user_home = url_for('login_successed', account=account_input, password=user_password)
			return redirect(go_to_user_home)

		else:
			error = "帳號或密碼輸入錯誤"
			form = LoginForm()
			return render_template('login.html',form=form, error=error)

	else:
		error = "帳號或密碼輸入錯誤"
		form = LoginForm()
		#print(manager_detail)
		return render_template('login.html',form=form, error=error)

	conn.close()


#---------------------------------------------------------------------------------------------
#Forget password


def create_confirm_token(account_id, expires_in=3600):
	"""利用itsdangerous來生成令牌，透過current_app來取得目前flask參數['SECRET_KEY']的值:param expiration: 有效時間，單位為秒:return: 回傳令牌，參數為該註冊用戶的id"""
	s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
	return s.dumps({'user_id': account_id})

class ForgetForm(FlaskForm):
	account = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

@app.route('/forget_password/input', methods = ['GET', 'POST'])
def forget_input():
	form = ForgetForm()
	return render_template('forget_input.html', form=form)

@app.route('/forget_password/solution', methods = ['GET', 'POST'])
def forget_solution():

	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	account_input = request.form.get('account')

	cur.execute("SELECT email FROM loginlist WHERE account='{account}' ".format(account=account_input, ))
	select_email = cur.fetchone()
	print('select_email:',select_email)

	if (select_email==None):
		error = "帳號輸入錯誤"
		form = ForgetForm()
		return render_template('forget_input.html',form=form, error=error)

	else:
		cur.execute("SELECT id,password,email FROM loginlist WHERE account='{account}'".format(account=account_input, ))
		select_account = cur.fetchone()
		#he_password = select_account[1]
		reset_mail = select_account[2]

		account_id = select_account[0]

		token = create_confirm_token(account_id=account_id)

		msg = Message('您的密碼', sender=app.config['MAIL_USERNAME'], recipients=[reset_mail])
		msg.html = render_template('mail_reset_body.html', account=account_input, token=token, )
		mail.send(msg)
		return render_template('send_mail_success.html',reset_mail=reset_mail, )
	conn.close()


def validate_confirm_token(token):
	"""驗證回傳令牌是否正確，若正確則回傳True:param token:驗證令牌:return:回傳驗證是否正確，正確為True"""
	s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
	try:
		data = s.loads(token)  # 驗證
	except SignatureExpired:
		#  當時間超過的時候就會引發SignatureExpired錯誤
		return False
	except BadSignature:
		#  當驗證錯誤的時候就會引發BadSignature錯誤
		return False
	return data



class ForgetResetForm(FlaskForm):
	new_password = PasswordField('',validators=[DataRequired()],render_kw={'autofocus': True})
	new_password_again = PasswordField('',validators=[DataRequired()])


@app.route('/froget_reset/<account>/<token>', methods = ['GET', 'POST'])
def forget_reset(account,token):
	data = validate_confirm_token(token)
	if data:
		form = ForgetResetForm()
		#reset_solution_url = '/forget/reset/<{account}>/solution'.format(account=account)
		return render_template('forget_reset_input.html', form=form, account=account, )
	else:
		return render_template('wrong_token.html')



@app.route('/froget_reset/<account>/solution', methods = ['GET', 'POST'])
def forget_reset_solution(account):

	new_password = request.form.get('new_password')
	new_password_again = request.form.get('new_password_again')

	if (new_password!=new_password_again):
		error = '兩次密碼輸入不一樣'
		form = ForgetResetForm()
		return render_template('forget_reset_input.html', form=form, account=account, error=error, )

	else:
		conn = psycopg2.connect(database="d5pdiejktvknug", user="aenplcguyghqsr", password="d4150af71b02722634f0729b96db7cd591fb92381527917b5c8757abe990cbba", host="ec2-107-21-98-165.compute-1.amazonaws.com", port="5432")
		cur = conn.cursor()

		cur.execute("UPDATE loginlist SET password='{new_password}' WHERE account='{account}'".format(new_password=new_password, account=account, ))
		conn.commit()
		error = "更新成功！"
		form = LoginForm()
		cur.execute("SELECT * FROM loginlist WHERE account='{account}'".format(account=account,))

		return render_template('login.html',form=form, error=error)
	conn.close()




#---------------------------------------------------------------
#Search Book

class SearchForm(FlaskForm):
	key_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})


@app.route('/search', methods = ['GET', 'POST'])
def search():
    form = SearchForm()
    return render_template('search_input.html',title = 'Search',form=form)


@app.route('/search_solution', methods=['POST'])
def search_solution():

	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	key_word = request.form.get('key_word')

	cur.execute("SELECT book_id, book_name, publisher, if_borrow FROM booklist WHERE book_name LIKE '%{keyword}%' OR book_id LIKE '%{key}%' ORDER BY if_borrow, book_id ASC".format(keyword=key_word,key=key_word ))
	search_book = cur.fetchall()

	if (search_book==[]):
		error = "我們找不到{key_word}".format(key_word=key_word)
		form = SearchForm()
		return render_template('search_input.html',form=form, error=error)

	else:
		return render_template(
			'search_solution.html',
			search_book=search_book,
	)

		conn.close()

#---------------------------------------------------------------
#Borrow Book

class Borrow_Peo_Form(FlaskForm):
	people_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

class Borrow_Book_Form(FlaskForm):
	book_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})


@app.route('/borrow/people_id/input/<account>/<password>', methods = ['GET', 'POST'])
def borrow_peo(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = Borrow_Peo_Form()
			back_home = '管理者'
			return render_template('borrow_peo_id_input.html',form=form, account=account, password=password, back_home=back_home, peo_word='0', the_book='0')
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = Borrow_Peo_Form()
			back_home = '使用者'
			return render_template('borrow_peo_id_input.html',form=form, account=account, password=password, back_home=back_home, peo_word='0', the_book='0')
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/borrow/book_id/input/<account>/<password>/<peo_word>/<the_book>', methods = ['GET', 'POST'])
def borrow_book(account,password,peo_word,the_book):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			if (peo_word!='0'):
				borrow_peo_id = peo_word

				cur.execute("SELECT * FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
				b = cur.fetchone()

				if (b==None):
					form = Borrow_Peo_Form()
					back_home = '管理者'
					error='資料裡沒有{peo_id}這個成員'.format(peo_id=borrow_peo_id)
					borrow_peo_id = '0'
					the_book = '0'
					return render_template('borrow_peo_id_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=borrow_peo_id,the_book=the_book, )

				else:
					cur.execute("SELECT book_name FROM booklist WHERE book_id='{the_book}'".format(the_book=the_book, ))
					the_book_name = cur.fetchone()

					error = '{the_book}--{the_book_name}：借書成功！'.format(the_book=the_book, the_book_name=the_book_name[0], )


					cur.execute("SELECT id FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					peo_bor_book_number = cur.fetchall()

					cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
					bor_peo_id, bor_peo_sta, bor_peo_class, bor_peo_name = cur.fetchone()

					cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_book = cur.fetchall()

					form = Borrow_Book_Form()
					back_home = '管理者'
					return render_template('borrow_book_id_input.html', error=error, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_class, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, account=account, password=password, back_home=back_home,  )

			else:

				borrow_peo_id = request.form.get('people_word')

				cur.execute("SELECT * FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
				b = cur.fetchone()

				if (b==None):
					form = Borrow_Peo_Form()
					back_home = '管理者'
					error='資料裡沒有{peo_id}這個成員'.format(peo_id=borrow_peo_id)
					borrow_peo_id = '0'
					the_book = '0'
					return render_template('borrow_peo_id_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=borrow_peo_id, the_book=the_book, )

				else:
					cur.execute("SELECT id FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					peo_bor_book_number = cur.fetchall()

					cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
					bor_peo_id, bor_peo_sta, bor_peo_class, bor_peo_name = cur.fetchone()

					cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_book = cur.fetchall()

					form = Borrow_Book_Form()
					back_home = '管理者'
					return render_template('borrow_book_id_input.html',form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_class, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, account=account, password=password, back_home=back_home,  )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			if (peo_word!='0'):
				borrow_peo_id = peo_word

				cur.execute("SELECT * FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
				b = cur.fetchone()

				if (b==None):
					form = Borrow_Peo_Form()
					back_home = '使用者'
					error='資料裡沒有{peo_id}這個成員'.format(peo_id=borrow_peo_id)
					borrow_peo_id = '0'
					the_book = '0'
					return render_template('borrow_peo_id_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=borrow_peo_id,the_book=the_book, )

				else:
					cur.execute("SELECT book_name FROM booklist WHERE book_id='{the_book}'".format(the_book=the_book, ))
					the_book_name = cur.fetchone()

					error = '{the_book}--{the_book_name}：借書成功！'.format(the_book=the_book, the_book_name=the_book_name[0], )


					cur.execute("SELECT id FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					peo_bor_book_number = cur.fetchall()

					cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
					bor_peo_id, bor_peo_sta, bor_peo_class, bor_peo_name = cur.fetchone()

					cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_book = cur.fetchall()

					form = Borrow_Book_Form()
					back_home = '使用者'
					return render_template('borrow_book_id_input.html', error=error, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_class, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, account=account, password=password, back_home=back_home,  )

			else:

				borrow_peo_id = request.form.get('people_word')

				cur.execute("SELECT * FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
				b = cur.fetchone()

				if (b==None):
					form = Borrow_Peo_Form()
					back_home = '使用者'
					error='資料裡沒有{peo_id}這個成員'.format(peo_id=borrow_peo_id)
					borrow_peo_id = '0'
					the_book = '0'
					return render_template('borrow_peo_id_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=borrow_peo_id, the_book=the_book, )

				else:
					cur.execute("SELECT id FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					peo_bor_book_number = cur.fetchall()

					cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
					bor_peo_id, bor_peo_sta, bor_peo_class, bor_peo_name = cur.fetchone()

					cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_book = cur.fetchall()

					form = Borrow_Book_Form()
					back_home = '使用者'
					return render_template('borrow_book_id_input.html',form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_class, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, account=account, password=password, back_home=back_home,  )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/borrow_solution/<account>/<password>', methods=['POST','GET'])
def borrow_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			borrow_book_id = request.form.get('book_word')
			borrow_peo_id = request.form.get('peo_word')

			cur.execute("SELECT * FROM booklist WHERE book_id = '{bookid}'".format(bookid=borrow_book_id, ))
			a = cur.fetchone()

			cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
			print_bor_book = cur.fetchall()

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
			bor_peo_id, bor_peo_sta, bor_peo_cla, bor_peo_name = cur.fetchone()

			if (a==None):
				form = Borrow_Book_Form()
				back_home = '管理者'
				error='資料裡沒有{book_id}這本書'.format(book_id=borrow_book_id)
				return render_template('borrow_solution.html',account=account,password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, error=error, back_home=back_home, )


			else:
				cur.execute("SELECT book_name, if_borrow, publisher FROM booklist WHERE book_id = '{bookid}'".format(bookid=borrow_book_id, ))
				bor_book_name, bor_book_ifborrow ,bor_publisher= cur.fetchone()

				cur.execute("SELECT id FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
				bor_book_num = len(cur.fetchall())

				cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
				print_bor_book = cur.fetchall()

				if (bor_book_ifborrow=='已借出'):
					form = Borrow_Book_Form()
					back_home = '管理者'
					error='{book_id}已被借出'.format(book_id=borrow_book_id)
					return render_template('borrow_solution.html', account=account, password=password, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, error=error, back_home=back_home, )

				elif (bor_book_name==None):
					error = '未找到{borrow_book_id}此本書'.format(borrow_book_id=borrow_book_id, )
					form = Borrow_Book_Form()
					back_home = '管理者'
					return render_template('borrow_solution.html', account=account, password=password, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, error=error, back_home=back_home, )

				elif (bor_peo_sta=='學生' or bor_peo_sta=='家長'):
					if (bor_book_num>=2):
						error='{peo_name}已達借書上限'.format(peo_name=bor_peo_name)
						form = Borrow_Peo_Form()
						back_home = '管理者'
						peo_word = '0'
						the_book = '0'
						return render_template('borrow_peo_id_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=peo_word, the_book=the_book, )

					else:
						#bor_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) -----此為import time 的方法
						time_now = datetime.datetime.now()
						bor_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )
						cur.execute(
							"UPDATE booklist SET if_borrow='已借出',"
							"people_id='{peo_id}', borrow_status='{bor_sta}', "
							"borrow_class='{bor_cla}', "
							"people_name='{peo_name}', borrow_time='{bor_time}' "
							"WHERE book_id='{bookid}'".format(peo_id=bor_peo_id, bor_sta=bor_peo_sta, bor_cla=bor_peo_cla, peo_name=bor_peo_name, bor_time=bor_time, bookid=borrow_book_id, ))
						conn.commit()

						cur.execute("INSERT INTO history (borrow_time,book_id,book_name,if_borrow,people_id,people_status,people_class,people_name,publisher) "
							"VALUES ('{borrow_time}','{borrow_book_id}','{bor_book_name}', "
							"'借出','{borrow_peo_id}','{bor_peo_sta}','{bor_peo_cla}',"
							"'{bor_peo_name}','{bor_publisher}')".format(borrow_time=bor_time, borrow_book_id=borrow_book_id, bor_book_name=bor_book_name, borrow_peo_id=borrow_peo_id, bor_peo_sta=bor_peo_sta, bor_peo_cla=bor_peo_cla, bor_peo_name=bor_peo_name, bor_publisher=bor_publisher, ))
						conn.commit()

						cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
						print_bor_book = cur.fetchall()

						form = Borrow_Book_Form()
						if form.validate_on_submit():
							return redirect(url_for('borrow_book', account=account, password=password, peo_word=borrow_peo_id, the_book=borrow_book_id, ))
						else:
							pass


						back_home = '管理者'
						return render_template('borrow_solution.html', account=account, password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, back_home=back_home, )

				else:
					time_now = datetime.datetime.now()
					bor_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )

					cur.execute(
						"UPDATE booklist SET if_borrow='已借出',"
						"people_id='{peo_id}', borrow_status='{bor_sta}', "
						"borrow_class='{bor_cla}', "
						"people_name='{peo_name}', borrow_time='{bor_time}' "
						"WHERE book_id='{bookid}'".format(peo_id=bor_peo_id, bor_sta=bor_peo_sta, bor_cla=bor_peo_cla, peo_name=bor_peo_name, bor_time=bor_time, bookid=borrow_book_id, ))
					conn.commit()

					cur.execute("INSERT INTO history (borrow_time,book_id,book_name,if_borrow,people_id,people_status,people_class,people_name,publisher) "
							"VALUES ('{borrow_time}','{borrow_book_id}','{bor_book_name}', "
							"'借出','{borrow_peo_id}','{bor_peo_sta}','{bor_peo_cla}', "
							"'{bor_peo_name}','{bor_publisher}')".format(borrow_time=bor_time, borrow_book_id=borrow_book_id, bor_book_name=bor_book_name, borrow_peo_id=borrow_peo_id, bor_peo_sta=bor_peo_sta, bor_peo_cla=bor_peo_cla, bor_peo_name=bor_peo_name, bor_publisher=bor_publisher, ))
					conn.commit()

					cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_book = cur.fetchall()

					form = Borrow_Book_Form()

					#print(form.validate_on_submit())

					if form.validate_on_submit():
						return redirect(url_for('borrow_book', account=account, password=password, peo_word=borrow_peo_id, the_book=borrow_book_id, ))
					else:
						pass


					back_home = '管理者'
					return render_template('borrow_solution.html', account=account, password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, back_home=back_home, )

				conn.close()
				conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			borrow_book_id = request.form.get('book_word')
			borrow_peo_id = request.form.get('peo_word')

			cur.execute("SELECT * FROM booklist WHERE book_id = '{bookid}'".format(bookid=borrow_book_id, ))
			a = cur.fetchone()

			cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
			print_bor_book = cur.fetchall()

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
			bor_peo_id, bor_peo_sta, bor_peo_cla, bor_peo_name = cur.fetchone()

			if (a==None):
				form = Borrow_Book_Form()
				back_home = '使用者'
				error='資料裡沒有{book_id}這本書'.format(book_id=borrow_book_id)
				return render_template('borrow_solution.html',account=account,password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, error=error, back_home=back_home, )


			else:
				cur.execute("SELECT book_name, if_borrow, publisher FROM booklist WHERE book_id = '{bookid}'".format(bookid=borrow_book_id, ))
				bor_book_name, bor_book_ifborrow ,bor_publisher= cur.fetchone()

				cur.execute("SELECT id FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
				bor_book_num = len(cur.fetchall())

				cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
				print_bor_book = cur.fetchall()

				if (bor_book_ifborrow=='已借出'):
					form = Borrow_Book_Form()
					back_home = '使用者'
					error='{book_id}已被借出'.format(book_id=borrow_book_id)
					return render_template('borrow_solution.html', account=account, password=password, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, error=error, back_home=back_home, )

				elif (bor_book_name==None):
					error = '未找到{borrow_book_id}此本書'.format(borrow_book_id=borrow_book_id, )
					form = Borrow_Book_Form()
					back_home = '使用者'
					return render_template('borrow_solution.html', account=account, password=password, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, error=error, back_home=back_home, )

				elif (bor_peo_sta=='學生' or bor_peo_sta=='家長'):
					if (bor_book_num>=2):
						error='{peo_name}已達借書上限'.format(peo_name=bor_peo_name)
						form = Borrow_Peo_Form()
						back_home = '使用者'
						peo_word = '0'
						the_book = '0'
						return render_template('borrow_peo_id_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=peo_word, the_book=the_book, )

					else:
						#bor_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) -----此為import time 的方法
						time_now = datetime.datetime.now()
						bor_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )
						cur.execute(
							"UPDATE booklist SET if_borrow='已借出',"
							"people_id='{peo_id}', borrow_status='{bor_sta}', "
							"borrow_class='{bor_cla}', "
							"people_name='{peo_name}', borrow_time='{bor_time}' "
							"WHERE book_id='{bookid}'".format(peo_id=bor_peo_id, bor_sta=bor_peo_sta, bor_cla=bor_peo_cla, peo_name=bor_peo_name, bor_time=bor_time, bookid=borrow_book_id, ))
						conn.commit()

						cur.execute("INSERT INTO history (borrow_time,book_id,book_name,if_borrow,people_id,people_status,people_class,people_name,publisher) "
							"VALUES ('{borrow_time}','{borrow_book_id}','{bor_book_name}', "
							"'借出','{borrow_peo_id}','{bor_peo_sta}','{bor_peo_cla}',"
							"'{bor_peo_name}','{bor_publisher}')".format(borrow_time=bor_time, borrow_book_id=borrow_book_id, bor_book_name=bor_book_name, borrow_peo_id=borrow_peo_id, bor_peo_sta=bor_peo_sta, bor_peo_cla=bor_peo_cla, bor_peo_name=bor_peo_name, bor_publisher=bor_publisher, ))
						conn.commit()

						cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
						print_bor_book = cur.fetchall()

						form = Borrow_Book_Form()
						if form.validate_on_submit():
							return redirect(url_for('borrow_book', account=account, password=password, peo_word=borrow_peo_id, the_book=borrow_book_id, ))
						else:
							pass


						back_home = '使用者'
						return render_template('borrow_solution.html', account=account, password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, back_home=back_home, )

				else:
					time_now = datetime.datetime.now()
					bor_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )

					cur.execute(
						"UPDATE booklist SET if_borrow='已借出',"
						"people_id='{peo_id}', borrow_status='{bor_sta}', "
						"borrow_class='{bor_cla}', "
						"people_name='{peo_name}', borrow_time='{bor_time}' "
						"WHERE book_id='{bookid}'".format(peo_id=bor_peo_id, bor_sta=bor_peo_sta, bor_cla=bor_peo_cla, peo_name=bor_peo_name, bor_time=bor_time, bookid=borrow_book_id, ))
					conn.commit()

					cur.execute("INSERT INTO history (borrow_time,book_id,book_name,if_borrow,people_id,people_status,people_class,people_name,publisher) "
							"VALUES ('{borrow_time}','{borrow_book_id}','{bor_book_name}', "
							"'借出','{borrow_peo_id}','{bor_peo_sta}','{bor_peo_cla}', "
							"'{bor_peo_name}','{bor_publisher}')".format(borrow_time=bor_time, borrow_book_id=borrow_book_id, bor_book_name=bor_book_name, borrow_peo_id=borrow_peo_id, bor_peo_sta=bor_peo_sta, bor_peo_cla=bor_peo_cla, bor_peo_name=bor_peo_name, bor_publisher=bor_publisher, ))
					conn.commit()

					cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_book = cur.fetchall()

					form = Borrow_Book_Form()

					#print(form.validate_on_submit())

					if form.validate_on_submit():
						return redirect(url_for('borrow_book', account=account, password=password, peo_word=borrow_peo_id, the_book=borrow_book_id, ))
					else:
						pass


					back_home = '使用者'
					return render_template('borrow_solution.html', account=account, password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_book=print_bor_book, peo_word=borrow_peo_id, back_home=back_home, )

				conn.close()
				conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


#--------------------------------------------------------------------------
#Return Book

class Return_Book_Form(FlaskForm):
	book_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})


@app.route('/return/book_id/input/<account>/<password>', methods = ['GET', 'POST'])
def return_book(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = Return_Book_Form()
			back_home = '管理者'
			submit_empty = '0'
			the_book = '0'
			return render_template('return_book_id_input.html',form=form, account=account, password=password, back_home=back_home, submit_empty=submit_empty, the_book=the_book, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = Return_Book_Form()
			back_home = '使用者'
			submit_empty = '0'
			the_book = '0'
			return render_template('return_book_id_input.html',form=form, account=account, password=password, back_home=back_home, submit_empty=submit_empty, the_book=the_book, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/return_solution/<account>/<password>/<submit_empty>/<the_book>', methods=['POST','GET'])
def return_solution(account,password,submit_empty,the_book):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			if (submit_empty!='0'):
				cur.execute("SELECT book_name FROM booklist WHERE book_id='{the_book}'".format(the_book=the_book, ))
				the_book_name = cur.fetchone()

				error = '{the_book}--{the_book_name}：還書成功！'.format(the_book=the_book, the_book_name=the_book_name[0], )
				form = Return_Book_Form()
				back_home = '管理者'

				cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=submit_empty))
				print_ret_book = cur.fetchall()

				cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=submit_empty, ))
				ret_peo_id, ret_peo_sta, ret_peo_cla, ret_peo_name = cur.fetchone()

				submit_empty = '0'
				the_book = '0'
				return render_template('return_solution.html', error=error, form=form, peo_id=ret_peo_id, peo_sta=ret_peo_sta, peo_class=ret_peo_cla, peo_name=ret_peo_name, peo_word=ret_peo_id, account=account, password=password, back_home=back_home, print_ret_book=print_ret_book, submit_empty=submit_empty, the_book=the_book, )


			else:
				return_book_id = request.form.get('book_word')

				cur.execute("SELECT book_name, if_borrow, people_id, borrow_status, borrow_class, people_name, borrow_time FROM booklist WHERE book_id = '{bookid}'".format(bookid=return_book_id, ))
				a = cur.fetchone()

				if(a==None):
					error='資料裡沒有{book_id}這本書'.format(book_id=return_book_id)
					form = Return_Book_Form()
					back_home = '管理者'
					submit_empty = '0'
					the_book = '0'
					return render_template('return_book_id_input.html',the_book=the_book, form=form, account=account, password=password, back_home=back_home, error=error, submit_empty=submit_empty, )

				else:
					cur.execute("SELECT book_name, if_borrow, people_id, borrow_status, borrow_class, people_name, borrow_time FROM booklist WHERE book_id = '{bookid}'".format(bookid=return_book_id, ))
					ret_book_name, ret_book_ifborrow, ret_peo_id, ret_peo_sta, ret_peo_cla, ret_peo_name, bor_time = cur.fetchone()

					if (ret_book_ifborrow=='未借出'):
						error='{book_id}未被借出'.format(book_id=return_book_id)
						form = Return_Book_Form()
						back_home = '管理者'
						submit_empty = '0'
						the_book = '0'
						return render_template('return_book_id_input.html', the_book=the_book, form=form, account=account, password=password, back_home=back_home, error=error, submit_empty=submit_empty )


					else:
						cur.execute("UPDATE booklist SET if_borrow='未借出', people_id=Null, borrow_status=Null, borrow_class=Null, people_name=Null, borrow_time=Null WHERE book_id='{bookid}'".format( bookid=return_book_id, ))
						conn.commit()

						cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=ret_peo_id))
						print_ret_book = cur.fetchall()

						time_now = datetime.datetime.now()
						ret_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )

						cur.execute("INSERT INTO history (borrow_time,book_id,book_name,if_borrow,people_id,people_status,people_class,people_name) "
							"VALUES ('{return_time}','{return_book_id}','{ret_book_name}', "
							"'還書','{return_peo_id}','{ret_peo_sta}','{ret_peo_cla}', "
							"'{ret_peo_name}')".format(return_time=ret_time, return_book_id=return_book_id, ret_book_name=ret_book_name, return_peo_id=ret_peo_id, ret_peo_sta=ret_peo_sta, ret_peo_cla=ret_peo_cla, ret_peo_name=ret_peo_name, ))
						conn.commit()

						form = Return_Book_Form()


						if form.validate_on_submit():
							return redirect(url_for('return_solution',account=account,password=password, submit_empty=ret_peo_id, the_book=return_book_id, ))
							#傳送submit_empty是為了顯示出還書的人剩哪些書沒還
						else:
							pass

						back_home = '管理者'
						return render_template('return_solution.html',form=form, peo_id=ret_peo_id, peo_sta=ret_peo_sta, peo_class=ret_peo_cla, peo_name=ret_peo_name, peo_word=ret_peo_id, account=account, password=password, back_home=back_home, print_ret_book=print_ret_book, )


				conn.close()
				conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			if (submit_empty!='0'):
				cur.execute("SELECT book_name FROM booklist WHERE book_id='{the_book}'".format(the_book=the_book, ))
				the_book_name = cur.fetchone()

				error = '{the_book}--{the_book_name}：還書成功！'.format(the_book=the_book, the_book_name=the_book_name[0], )
				form = Return_Book_Form()
				back_home = '使用者'

				cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=submit_empty))
				print_ret_book = cur.fetchall()

				cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=submit_empty, ))
				ret_peo_id, ret_peo_sta, ret_peo_cla, ret_peo_name = cur.fetchone()

				submit_empty = '0'
				the_book = '0'
				return render_template('return_solution.html', error=error, form=form, peo_id=ret_peo_id, peo_sta=ret_peo_sta, peo_class=ret_peo_cla, peo_name=ret_peo_name, peo_word=ret_peo_id, account=account, password=password, back_home=back_home, print_ret_book=print_ret_book, submit_empty=submit_empty, the_book=the_book, )


			else:
				return_book_id = request.form.get('book_word')

				cur.execute("SELECT book_name, if_borrow, people_id, borrow_status, borrow_class, people_name, borrow_time FROM booklist WHERE book_id = '{bookid}'".format(bookid=return_book_id, ))
				a = cur.fetchone()

				if(a==None):
					error='資料裡沒有{book_id}這本書'.format(book_id=return_book_id)
					form = Return_Book_Form()
					back_home = '使用者'
					submit_empty = '0'
					the_book = '0'
					return render_template('return_book_id_input.html',the_book=the_book, form=form, account=account, password=password, back_home=back_home, error=error, submit_empty=submit_empty, )

				else:
					cur.execute("SELECT book_name, if_borrow, people_id, borrow_status, borrow_class, people_name, borrow_time FROM booklist WHERE book_id = '{bookid}'".format(bookid=return_book_id, ))
					ret_book_name, ret_book_ifborrow, ret_peo_id, ret_peo_sta, ret_peo_cla, ret_peo_name, bor_time = cur.fetchone()

					if (ret_book_ifborrow=='未借出'):
						error='{book_id}未被借出'.format(book_id=return_book_id)
						form = Return_Book_Form()
						back_home = '使用者'
						submit_empty = '0'
						the_book = '0'
						return render_template('return_book_id_input.html', the_book=the_book, form=form, account=account, password=password, back_home=back_home, error=error, submit_empty=submit_empty )


					else:
						cur.execute("UPDATE booklist SET if_borrow='未借出', people_id=Null, borrow_status=Null, borrow_class=Null, people_name=Null, borrow_time=Null WHERE book_id='{bookid}'".format( bookid=return_book_id, ))
						conn.commit()

						cur.execute("SELECT book_id, book_name, borrow_time FROM booklist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=ret_peo_id))
						print_ret_book = cur.fetchall()

						time_now = datetime.datetime.now()
						ret_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )

						cur.execute("INSERT INTO history (borrow_time,book_id,book_name,if_borrow,people_id,people_status,people_class,people_name) "
							"VALUES ('{return_time}','{return_book_id}','{ret_book_name}', "
							"'還書','{return_peo_id}','{ret_peo_sta}','{ret_peo_cla}', "
							"'{ret_peo_name}')".format(return_time=ret_time, return_book_id=return_book_id, ret_book_name=ret_book_name, return_peo_id=ret_peo_id, ret_peo_sta=ret_peo_sta, ret_peo_cla=ret_peo_cla, ret_peo_name=ret_peo_name, ))
						conn.commit()

						form = Return_Book_Form()


						if form.validate_on_submit():
							return redirect(url_for('return_solution',account=account,password=password, submit_empty=ret_peo_id, the_book=return_book_id, ))
							#傳送submit_empty是為了顯示出還書的人剩哪些書沒還
						else:
							pass

						back_home = '使用者'
						return render_template('return_solution.html',form=form, peo_id=ret_peo_id, peo_sta=ret_peo_sta, peo_class=ret_peo_cla, peo_name=ret_peo_name, peo_word=ret_peo_id, account=account, password=password, back_home=back_home, print_ret_book=print_ret_book, )


				conn.close()
				conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


#------------------------------------------------------------------
#Unreturn Book

class UnreturnForm(FlaskForm):
	key_word = StringField('', description=['可輸入書目編碼、書名、成員編碼、成員姓名、成員班級、成員身份等關鍵字。'],validators=[DataRequired()],render_kw={'autofocus': True}, )
	keyword_or_all = SelectField('', choices=[('keyword', '關鍵字'),('all', '全部相同'),])


@app.route('/unreturn/<account>/<password>', methods = ['GET', 'POST'])
def unreturn(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = UnreturnForm()
			back_home = '管理者'
			return render_template('unreturn_input.html', form=form, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/unreturn_solution/<account>/<password>', methods=['GET', 'POST'])
def unreturn_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			key_word = request.form.get('key_word')
			keyword_or_all = request.form.get('keyword_or_all')

			if (keyword_or_all=='keyword'):
				cur.execute(
					"SELECT * "
					"FROM booklist "
					"WHERE if_borrow='已借出' AND (book_name LIKE '%{keyword}%' "
					"OR book_id LIKE '%{keyword}%' OR people_id LIKE '%{keyword}%'"
					"OR people_name LIKE '%{keyword}%' OR borrow_class LIKE '%{keyword}%'"
					"OR borrow_status LIKE '%{keyword}%') ORDER BY borrow_class, people_name DESC".format(keyword=key_word, ))

				unreturn_book = cur.fetchall()

			else:
				cur.execute("SELECT * FROM booklist "
					"WHERE if_borrow='已借出' AND (book_name='{keyword}' "
					"OR book_id='{keyword}' OR people_id='{keyword}' "
					"OR people_name='{keyword}' OR borrow_class='{keyword}' "
					"OR borrow_status='{keyword}') ORDER BY borrow_class, people_name DESC".format(keyword=key_word, ))
				unreturn_book = cur.fetchall()

			if (unreturn_book==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = UnreturnForm()
				back_home = '管理者'
				return render_template('unreturn_input.html',form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				back_home = '管理者'
				return render_template('unreturn_solution.html',unreturn_book=unreturn_book,account=account, password=password, back_home=back_home, )


			conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			key_word = request.form.get('key_word')
			keyword_or_all = request.form.get('keyword_or_all')

			if (keyword_or_all=='keyword'):
				cur.execute(
					"SELECT * "
					"FROM booklist "
					"WHERE if_borrow='已借出' AND (book_name LIKE '%{keyword}%' "
					"OR book_id LIKE '%{keyword}%' OR people_id LIKE '%{keyword}%'"
					"OR people_name LIKE '%{keyword}%' OR borrow_class LIKE '%{keyword}%'"
					"OR borrow_status LIKE '%{keyword}%') ORDER BY borrow_class, people_name DESC".format(keyword=key_word, ))

				unreturn_book = cur.fetchall()

			else:
				cur.execute("SELECT * FROM booklist "
					"WHERE if_borrow='已借出' AND (book_name='{keyword}' "
					"OR book_id='{keyword}' OR people_id='{keyword}' "
					"OR people_name='{keyword}' OR borrow_class='{keyword}' "
					"OR borrow_status='{keyword}') ORDER BY borrow_class, people_name DESC".format(keyword=key_word, ))
				unreturn_book = cur.fetchall()

			if (unreturn_book==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = UnreturnForm()
				back_home = '使用者'
				return render_template('unreturn_input.html',form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				back_home = '使用者'
				return render_template('unreturn_solution.html',unreturn_book=unreturn_book,account=account, password=password, back_home=back_home, )

			conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/unreturn_all/<account>/<password>', methods=['GET', 'POST'])
def unreturn_all(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM booklist WHERE if_borrow='已借出' ORDER BY borrow_class, people_name DESC")
			all_unreturn_book = cur.fetchall()
			back_home = '管理者'
			return render_template('unreturn_solution.html',unreturn_book=all_unreturn_book,account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			cur.execute("SELECT * FROM booklist WHERE if_borrow='已借出' ORDER BY borrow_class, people_name DESC")
			all_unreturn_book = cur.fetchall()
			back_home = '使用者'
			return render_template('unreturn_solution.html',unreturn_book=all_unreturn_book,account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)





#----------------------------------------------------------------------------------
#Manager Book And Delete Book

class ManageBookForm(FlaskForm):
	account = StringField('',validators=[DataRequired()], render_kw={'autofocus': True})
	password = StringField('',validators=[DataRequired()])


@app.route('/manager_book/choose/<account>/<password>')
def book_choose(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			back_home = '管理者'
			return render_template('book_choose.html', account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			back_home = '使用者'
			return render_template('book_choose.html', account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


class DeleteBook_Search_Form(FlaskForm):
	key_word = StringField('',validators=[DataRequired()], render_kw={'autofocus': True}, )

@app.route('/delete_book/search/<account>/<password>', methods = ['GET', 'POST'])
def delete_book_search(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = DeleteBook_Search_Form()
			back_home = '管理者'
			return render_template('delete_book_search.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = DeleteBook_Search_Form()
			back_home = '使用者'
			return render_template('delete_book_search.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)

class DeleteBook_Input_Form(FlaskForm):
	book_id_input = StringField('', validators=[DataRequired()], render_kw={'autofocus': True}, )

@app.route('/delete_book/input/<account>/<password>', methods = ['GET', 'POST'])
def delete_book_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			key_word = request.form.get('key_word')

			cur.execute(
				"SELECT book_id, book_name, if_borrow, publisher,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM booklist "
				"WHERE book_name LIKE '%{keyword}%' "
				"OR book_id LIKE '%{keyword}%' ORDER BY book_id ASC".format(keyword=key_word, ))

			search_book = cur.fetchall()

			if (search_book==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = DeleteBook_Search_Form()
				back_home = '管理者'
				return render_template('delete_book_search.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				form = DeleteBook_Input_Form()
				back_home = '管理者'
				return render_template('delete_book_input.html', form=form, search_book=search_book, key_word=key_word, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			key_word = request.form.get('key_word')

			cur.execute(
				"SELECT book_id, book_name, if_borrow, publisher,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM booklist "
				"WHERE book_name LIKE '%{keyword}%' "
				"OR book_id LIKE '%{keyword}%' ORDER BY book_id ASC".format(keyword=key_word, ))

			search_book = cur.fetchall()

			if (search_book==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = DeleteBook_Search_Form()
				back_home = '使用者'
				return render_template('delete_book_search.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				form = DeleteBook_Input_Form()
				back_home = '使用者'
				return render_template('delete_book_input.html', form=form, search_book=search_book, key_word=key_word, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/delete_book/sure/<account>/<password>/<key_word>', methods = ['GET', 'POST'])
def delete_book_sure(account,password,key_word):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			book_id_input = request.form.get('book_id_input')

			cur.execute("SELECT * FROM booklist WHERE book_id='{book_id_input}'".format(book_id_input=book_id_input))
			select_delete_book = cur.fetchone()

			cur.execute(
				"SELECT book_id, book_name, if_borrow,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM booklist "
				"WHERE book_name LIKE '%{keyword}%' "
				"OR book_id LIKE '%{keyword}%'".format(keyword=key_word, ))
			search_book = cur.fetchall()

			if (select_delete_book==None):
				form = DeleteBook_Input_Form()
				back_home = '管理者'
				error = '資料裡沒有{book_id_input}這本書'.format(book_id_input=book_id_input, )
				return render_template('delete_book_input.html', form=form, search_book=search_book, account=account, password=password, back_home=back_home, error=error, key_word=key_word, )

			else:
				select_book_id = select_delete_book[1]
				back_home = '管理者'
				return render_template('delete_book_sure.html', select_delete_book=select_delete_book, select_book_id=select_book_id, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			book_id_input = request.form.get('book_id_input')

			cur.execute("SELECT * FROM booklist WHERE book_id='{book_id_input}'".format(book_id_input=book_id_input))
			select_delete_book = cur.fetchone()

			cur.execute(
				"SELECT book_id, book_name, if_borrow,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM booklist "
				"WHERE book_name LIKE '%{keyword}%' "
				"OR book_id LIKE '%{keyword}%'".format(keyword=key_word, ))
			search_book = cur.fetchall()

			if (select_delete_book==None):
				form = DeleteBook_Input_Form()
				back_home = '使用者'
				error = '資料裡沒有{book_id_input}這本書'.format(book_id_input=book_id_input, )
				return render_template('delete_book_input.html', form=form, search_book=search_book, account=account, password=password, back_home=back_home, error=error, key_word=key_word, )

			else:
				select_book_id = select_delete_book[1]
				back_home = '使用者'
				return render_template('delete_book_sure.html', select_delete_book=select_delete_book, select_book_id=select_book_id, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/delete_book/solution/<account>/<password>/<select_book_id>', methods = ['GET', 'POST'])
def delete_book_solution(account,password,select_book_id):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM booklist WHERE book_id='{select_book_id}'".format(select_book_id=select_book_id, ))
			select_book = cur.fetchone()

			cur.execute("DELETE FROM booklist "
				"WHERE book_id='{select_book_id}'".format(select_book_id=select_book_id, ))
			conn.commit()
			back_home = '管理者'
			return render_template('delete_book_success.html', select_book=select_book, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			cur.execute("SELECT * FROM booklist WHERE book_id='{select_book_id}'".format(select_book_id=select_book_id, ))
			select_book = cur.fetchone()

			cur.execute("DELETE FROM booklist "
				"WHERE book_id='{select_book_id}'".format(select_book_id=select_book_id, ))
			conn.commit()
			back_home = '使用者'
			return render_template('delete_book_success.html', select_book=select_book, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


#--------------------------------------------------------------------------------------
#查看全部書目的功能（實際上未使用）

@app.route('/all_book/<account>/<password>', methods = ['GET', 'POST'])
def all_book(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			cur.execute("SELECT * FROM booklist WHERE id!='1' ORDER BY book_id ASC")
			all_book = cur.fetchall()
			back_home = '管理者'
			return render_template('all_book.html',account=account,password=password, all_book=all_book, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)





#--------------------------------------------------------------------------------------
#Insert Book

class InsertBookForm(FlaskForm):
	insert_book_id = StringField('', description=['編碼開頭必須為Ｂ，後面加上五碼數字'], validators=[DataRequired()], render_kw={'autofocus': True})
	insert_book_name = StringField('',validators=[DataRequired()])
	insert_book_publisher = StringField('',validators=[DataRequired()])


@app.route('/insert_book/input/<account>/<password>', methods = ['GET', 'POST'])
def insert_book_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			form = InsertBookForm()
			back_home = '管理者'
			return render_template('insert_book_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			form = InsertBookForm()
			back_home = '使用者'
			return render_template('insert_book_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/insert_book/solution/<account>/<password>', methods = ['GET', 'POST'])
def insert_book_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			book_id_input = request.form.get('insert_book_id')
			book_name_input = request.form.get('insert_book_name')
			book_publisher_input = request.form.get('insert_book_publisher')

			cur.execute("SELECT book_id,book_name FROM booklist WHERE book_id='{book_id_input}'".format(book_id_input=book_id_input, ))
			select_book = cur.fetchone()

			if (book_id_input[0]!='B' or len(book_id_input)!=6 or str.isdigit(book_id_input[1:])!=1):
				error = '書目編碼輸入錯誤！書目編碼需為6碼，且第1碼需為B後五碼需為數字！'.format(book_id_input=book_id_input)
				form = InsertBookForm()
				back_home = '管理者'
				return render_template('insert_book_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			elif (select_book!=None):
				error = '{book_id_input}已有書名'.format(book_id_input=book_id_input)
				form = InsertBookForm()
				back_home = '管理者'
				return render_template('insert_book_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else :
				cur.execute("INSERT INTO booklist (book_id,book_name,if_borrow,publisher) VALUES ('{book_id_input}','{book_name_input}','未借出','{book_publisher_input}')".format(book_id_input=book_id_input, book_name_input=book_name_input, book_publisher_input=book_publisher_input, ))
				conn.commit()

				cur.execute("SELECT * FROM booklist WHERE book_id='{book_id_input}'".format(book_id_input=book_id_input, ))
				print_insert_book = cur.fetchone()
				back_home = '管理者'
				return render_template('insert_book_success.html',print_insert_book=print_insert_book, account=account, password=password, back_home=back_home, )


		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			book_id_input = request.form.get('insert_book_id')
			book_name_input = request.form.get('insert_book_name')
			book_publisher_input = request.form.get('insert_book_publisher')

			cur.execute("SELECT book_id,book_name FROM booklist WHERE book_id='{book_id_input}'".format(book_id_input=book_id_input, ))
			select_book = cur.fetchone()

			if (book_id_input[0]!='B' or len(book_id_input)!=6 or str.isdigit(book_id_input[1:])!=1):
				error = '書目編碼輸入錯誤！書目編碼需為6碼，且第1碼需為B後五碼需為數字！'.format(book_id_input=book_id_input)
				form = InsertBookForm()
				back_home = '使用者'
				return render_template('insert_book_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			elif (select_book!=None):
				error = '{book_id_input}已有書名'.format(book_id_input=book_id_input)
				form = InsertBookForm()
				back_home = '使用者'
				return render_template('insert_book_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else :
				cur.execute("INSERT INTO booklist (book_id,book_name,if_borrow,publisher) VALUES ('{book_id_input}','{book_name_input}','未借出','{book_publisher_input}')".format(book_id_input=book_id_input, book_name_input=book_name_input, book_publisher_input=book_publisher_input, ))
				conn.commit()

				cur.execute("SELECT * FROM booklist WHERE book_id='{book_id_input}'".format(book_id_input=book_id_input, ))
				print_insert_book = cur.fetchone()
				back_home = '使用者'
				return render_template('insert_book_success.html',print_insert_book=print_insert_book, account=account, password=password, back_home=back_home, )


		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



#----------------------------------------------------------------------------------
#Manager People And Delete People

@app.route('/manager_people/choose/<account>/<password>')
def people_choose(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			back_home = '管理者'
			return render_template('people_choose.html', account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			back_home = '使用者'
			return render_template('people_choose.html', account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


class DeletePeo_Search_Form(FlaskForm):
	key_word = StringField('',validators=[DataRequired()], render_kw={'autofocus': True}, )

@app.route('/delete_peo/search/<account>/<password>', methods = ['GET', 'POST'])
def delete_peo_search(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = DeletePeo_Search_Form()
			back_home = '管理者'
			return render_template('delete_peo_search.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = DeletePeo_Search_Form()
			back_home = '使用者'
			return render_template('delete_peo_search.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



class DeletePeo_Input_Form(FlaskForm):
	peo_id_input = StringField('', validators=[DataRequired()], render_kw={'autofocus': True})

@app.route('/delete_peo/input/<account>/<password>', methods = ['GET', 'POST'])
def delete_peo_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			key_word = request.form.get('key_word')

			cur.execute(
				"SELECT *"
				"FROM peoplelist "
				"WHERE people_name LIKE '%{keyword}%' "
				"OR people_id LIKE '%{keyword}%'".format(keyword=key_word, ))

			search_peo = cur.fetchall()

			if (search_peo==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = DeletePeo_Search_Form()
				back_home = '管理者'
				return render_template('delete_peo_search.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				form = DeletePeo_Input_Form()
				back_home = '管理者'
				return render_template('delete_peo_input.html', form=form, search_peo=search_peo, key_word=key_word, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			key_word = request.form.get('key_word')

			cur.execute(
				"SELECT *"
				"FROM peoplelist "
				"WHERE people_name LIKE '%{keyword}%' "
				"OR people_id LIKE '%{keyword}%'".format(keyword=key_word, ))

			search_peo = cur.fetchall()

			if (search_peo==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = DeletePeo_Search_Form()
				back_home = '使用者'
				return render_template('delete_peo_search.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				form = DeletePeo_Input_Form()
				back_home = '使用者'
				return render_template('delete_peo_input.html', form=form, search_book=search_peo, key_word=key_word, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/delete_peo/sure/<account>/<password>/<key_word>', methods = ['GET', 'POST'])
def delete_peo_sure(account,password,key_word):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			peo_id_input = request.form.get('peo_id_input')

			cur.execute("SELECT * FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_id_input))
			select_delete_peo = cur.fetchone()

			cur.execute(
				"SELECT *"
				"FROM peoplelist "
				"WHERE people_name LIKE '%{keyword}%' "
				"OR people_id LIKE '%{keyword}%'".format(keyword=key_word, ))
			search_peo = cur.fetchall()

			if (select_delete_peo==None):
				form = DeletePeo_Input_Form()
				back_home = '管理者'
				error = '刪除編碼輸入錯誤'
				return render_template('delete_peo_input.html', form=form, search_peo=search_peo, account=account, password=password, back_home=back_home, error=error, key_word=key_word, )

			else:
				select_peo_id = select_delete_peo[1]
				back_home = '管理者'
				return render_template('delete_peo_sure.html', select_delete_peo=select_delete_peo, select_peo_id=select_peo_id, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			peo_id_input = request.form.get('peo_id_input')

			cur.execute("SELECT * FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_id_input))
			select_delete_peo = cur.fetchone()

			cur.execute(
				"SELECT *"
				"FROM peoplelist "
				"WHERE people_name LIKE '%{keyword}%' "
				"OR people_id LIKE '%{keyword}%'".format(keyword=key_word, ))
			search_peo = cur.fetchall()

			if (select_delete_peo==None):
				form = DeletePeo_Input_Form()
				back_home = '使用者'
				error = '刪除編碼輸入錯誤'
				return render_template('delete_peo_input.html', form=form, search_peo=search_peo, account=account, password=password, back_home=back_home, error=error, key_word=key_word, )

			else:
				select_peo_id = select_delete_peo[1]
				back_home = '使用者'
				return render_template('delete_peo_sure.html', select_delete_peo=select_delete_peo, select_peo_id=select_peo_id, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/delete_peo/solution/<account>/<password>/<select_peo_id>', methods = ['GET', 'POST'])
def delete_peo_solution(account,password,select_peo_id):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM peoplelist WHERE people_id='{select_peo_id}'".format(select_peo_id=select_peo_id, ))
			select_peo = cur.fetchone()

			cur.execute("DELETE FROM peoplelist " 
				"WHERE people_id='{select_peo_id}'".format(select_peo_id=select_peo_id, ))
			conn.commit()
			back_home = '管理者'
			return render_template('delete_peo_success.html', select_peo=select_peo, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			cur.execute("SELECT * FROM peoplelist WHERE people_id='{select_peo_id}'".format(select_peo_id=select_peo_id, ))
			select_peo = cur.fetchone()

			cur.execute("DELETE FROM peoplelist " 
				"WHERE people_id='{select_peo_id}'".format(select_peo_id=select_peo_id, ))
			conn.commit()
			back_home = '使用者'
			return render_template('delete_peo_success.html', select_peo=select_peo, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



#--------------------------------------------------------------------------------------
#Insert People

class InsertPeoForm(FlaskForm):
	insert_peo_id = StringField('', description=['編碼必須是五碼數字'],validators=[DataRequired()], render_kw={'autofocus': True})
	insert_peo_status = SelectField('', choices=[('老師', '老師'),('學生', '學生'),('家長', '家長'),])
	insert_peo_class = StringField('', validators=[DataRequired()])
	insert_peo_name = StringField('',validators=[DataRequired()])


@app.route('/insert_peo/input/<account>/<password>', methods = ['GET', 'POST'])
def insert_peo_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			form = InsertPeoForm()
			back_home = '管理者'
			return render_template('insert_peo_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			form = InsertPeoForm()
			back_home = '使用者'
			return render_template('insert_peo_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/insert_peo/solution/<account>/<password>', methods = ['GET', 'POST'])
def insert_peo_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			peo_id_input = request.form.get('insert_peo_id')
			peo_sta_input = request.form.get('insert_peo_status')
			peo_cla_input = request.form.get('insert_peo_class')
			peo_name_input = request.form.get('insert_peo_name')

			cur.execute("SELECT people_id,people_name FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_id_input, ))
			select_peo = cur.fetchone()

			id_is_number = str.isdigit(peo_id_input)

			if (len(peo_id_input)!=5 or id_is_number!=1):
				error = '成員編碼輸入錯誤！成員編碼需為5碼數字'.format(peo_id_input=peo_id_input)
				form = InsertPeoForm()
				back_home = '管理者'
				return render_template('insert_peo_input.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			elif (select_peo!=None):
				error = '{peo_id_input}已有成員'.format(peo_id_input=peo_id_input)
				form = InsertPeoForm()
				back_home = '管理者'
				return render_template('insert_peo_input.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				cur.execute("INSERT INTO peoplelist (people_id,people_status,people_class,people_name) VALUES ('{peo_id_input}','{peo_sta_input}','{peo_cla_input}','{peo_name_input}')".format(peo_id_input=peo_id_input, peo_sta_input=peo_sta_input, peo_cla_input=peo_cla_input, peo_name_input=peo_name_input, ))
				conn.commit()

				cur.execute("SELECT * FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_id_input, ))
				print_insert_peo = cur.fetchone()
				back_home = '管理者'
				return render_template('insert_peo_success.html',print_insert_peo=print_insert_peo, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			peo_id_input = request.form.get('insert_peo_id')
			peo_sta_input = request.form.get('insert_peo_status')
			peo_cla_input = request.form.get('insert_peo_class')
			peo_name_input = request.form.get('insert_peo_name')

			cur.execute("SELECT people_id,people_name FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_id_input, ))
			select_peo = cur.fetchone()

			id_is_number = str.isdigit(peo_id_input)

			if (len(peo_id_input)!=5 or id_is_number!=1):
				error = '成員編碼輸入錯誤！成員編碼需為5碼數字'.format(peo_id_input=peo_id_input)
				form = InsertPeoForm()
				back_home = '使用者'
				return render_template('insert_peo_input.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			elif (select_peo!=None):
				error = '{peo_id_input}已有成員'.format(peo_id_input=peo_id_input)
				form = InsertPeoForm()
				back_home = '使用者'
				return render_template('insert_peo_input.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				cur.execute("INSERT INTO peoplelist (people_id,people_status,people_class,people_name) VALUES ('{peo_id_input}','{peo_sta_input}','{peo_cla_input}','{peo_name_input}')".format(peo_id_input=peo_id_input, peo_sta_input=peo_sta_input, peo_cla_input=peo_cla_input, peo_name_input=peo_name_input, ))
				conn.commit()

				cur.execute("SELECT * FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_id_input, ))
				print_insert_peo = cur.fetchone()
				back_home = '使用者'
				return render_template('insert_peo_success.html',print_insert_peo=print_insert_peo, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



#-----------------------------------------------------------------------------------------
#成員搜尋

class Search_Peo_Form(FlaskForm):
	peo_key_word = StringField('',description=['可輸入想查詢的成員姓名、編碼、班級、身份等關鍵字'], validators=[DataRequired()],render_kw={'autofocus': True})

@app.route('/people_search/<account>/<password>', methods = ['GET', 'POST'])
def people_search(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = Search_Peo_Form()
			back_home = '管理者'
			return render_template('peo_search_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = Search_Peo_Form()
			back_home = '使用者'
			return render_template('peo_search_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/people_search/all/<account>/<password>', methods = ['GET', 'POST'])
def peo_search_all(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM peoplelist WHERE id!='1' ORDER BY people_id ASC")
			peo_search_all = cur.fetchall()

			conn.close()
			back_home = '管理者'
			return render_template('peo_detail.html', account=account, password=password, peo_search_all=peo_search_all, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			cur.execute("SELECT * FROM peoplelist WHERE id!='1' ORDER BY people_id ASC")
			peo_search_all = cur.fetchall()
			conn.close()
			back_home = '使用者'
			return render_template('peo_detail.html', account=account, password=password, peo_search_all=peo_search_all, back_home=back_home, )
			
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/people_search/solution/<account>/<password>', methods = ['GET', 'POST'])
def peo_search_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			peo_key_word = request.form.get('peo_key_word')

			cur.execute("SELECT * FROM peoplelist WHERE "
				"people_id LIKE '%{peo_key_word}%' OR people_status LIKE '%{peo_key_word}%' OR "
				"people_class LIKE '%{peo_key_word}%' OR "
				"people_name LIKE'%{peo_key_word}%'".format(peo_key_word=peo_key_word))
			peo_search_all = cur.fetchall()
			if (peo_search_all==[]):
				error = '我們找不到{peo_key_word}'.format(peo_key_word=peo_key_word, )
				form = Search_Peo_Form()
				back_home = '管理者'
				return render_template('peo_search_input.html', form=form, account=account, password=password, error=error, back_home=back_home, )
			else:
				back_home = '管理者'
				return render_template('peo_detail.html', peo_search_all=peo_search_all, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			peo_key_word = request.form.get('peo_key_word')

			cur.execute("SELECT * FROM peoplelist WHERE "
				"people_id LIKE '%{peo_key_word}%' OR people_status LIKE '%{peo_key_word}%' OR "
				"people_class LIKE '%{peo_key_word}%' OR "
				"people_name LIKE'%{peo_key_word}%'")
			peo_search_all = cur.fetchall()
			if (peo_search_all==[]):
				error = '我們找不到{peo_key_word}'.format(peo_key_word=peo_key_word, )
				form = Search_Peo_Form()
				back_home = '使用者'
				return render_template('peo_search_input.html', form=form, account=account, password=password, error=error, back_home=back_home, )
			else:
				back_home = '使用者'
				return render_template('peo_detail.html', peo_search_all=peo_search_all, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


#-----------------------------------------------------------------------------------
#歷史紀錄


class HistoryForm(FlaskForm):
	#peo_cla_input = StringField('', validators=[DataRequired()])
	#peo_name_input = StringField('', validators=[DataRequired()])
	peo_id_input = StringField('', validators=[DataRequired()],render_kw={'autofocus': True})

@app.route('/history_input/<account>/<password>', methods = ['GET', 'POST'])
def history_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = HistoryForm()
			back_home = '管理者'
			return render_template('history_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = HistoryForm()
			back_home = '使用者'
			return render_template('history_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/history_soultion/<account>/<password>', methods = ['GET', 'POST'])
def history_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			#peo_cla_input = request.form.get('peo_cla_input')
			#peo_name_input = request.form.get('peo_name_input')
			peo_id_input = request.form.get('peo_id_input')

			cur.execute("SELECT * FROM history WHERE people_id='{peo_id}' AND if_borrow='借出'".format(peo_id=peo_id_input))
			select_history = cur.fetchall()

			if (select_history==[]):
				error = '我們找不到成員編碼為{peo_id}歷史紀錄。'.format(peo_id=peo_id_input, )
				form = HistoryForm()
				back_home = '管理者'
				return render_template('history_input.html', form=form, account=account, password=password, error=error, back_home=back_home, )
			else:
				select_peo = select_history[0]
				back_home = '管理者'
				return render_template('history_solution.html', select_peo=select_peo, select_history=select_history, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			#peo_cla_input = request.form.get('peo_cla_input')
			#peo_name_input = request.form.get('peo_name_input')
			peo_id_input = request.form.get('peo_id_input')

			cur.execute("SELECT * FROM history WHERE people_id='{peo_id}' AND if_borrow='借出'".format(peo_id=peo_id_input))
			select_history = cur.fetchall()

			if (select_history==[]):
				error = '我們找不到成員編碼為{peo_id}歷史紀錄。'.format(peo_id=peo_id_input, )
				form = HistoryForm()
				back_home = '使用者'
				return render_template('history_input.html', form=form, account=account, password=password, error=error, back_home=back_home, )
			else:
				select_peo = select_history[0]
				back_home = '使用者'
				return render_template('history_solution.html', select_peo=select_peo, select_history=select_history, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)

#--------------------------------------------------------------------------
#目前沒有使用，可看全部的歷史紀錄

@app.route('/history_all/<account>/<password>', methods = ['GET', 'POST'])
def all_history(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM history")
			all_history = cur.fetchall()

			return render_template('all_history.html', account=account, password=password, all_history=all_history, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



#-------------------------------------------------------------------------------
#帳號管理（更改密碼或信箱）


class ChangeForm(FlaskForm):
	change_account = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

@app.route('/manager_change/input/<account>/<password>', methods = ['GET', 'POST'])
def manager_change_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = ChangeForm()
			back_home = '管理者'
			return render_template('change_account_input.html', form=form, account=account, password=password, back_home=back_home,)
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/manager_change/choose/<account>/<password>', methods = ['GET', 'POST'])
def manager_change_choose(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			change_account = request.form.get('change_account')


			cur.execute("SELECT * FROM loginlist WHERE account='{change_account}'".format(change_account=change_account, ))
			select_account = cur.fetchall()
			print(select_account)

			if (select_account==[]):
				error = '我們找不到{change_account}這個帳號'.format(change_account=change_account, )
				form = ChangeForm()
				back_home = '管理者'
				return render_template('change_account_input.html', form=form, account=account, password=password, error=error, back_home=back_home, )
			else:
				back_home = '管理者'
				return render_template('change_choose.html',account=account,password=password, change_account=change_account, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



class PasswordForm(FlaskForm):
	oringin_password = PasswordField('',validators=[DataRequired()],render_kw={'autofocus': True})
	new_password = PasswordField('',validators=[DataRequired()])
	new_password_again = PasswordField('',validators=[DataRequired()])


@app.route('/manager_change/password/<account>/<password>/<change_account>', methods = ['GET', 'POST'])
def manager_change_password(account,password, change_account):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			#change_account = request.form.get('change_account')

			form = PasswordForm()
			back_home = '管理者'
			return render_template('change_password_input.html', form=form, account=account, password=password, change_account=change_account, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)





@app.route('/manager_change/solution/<account>/<password>/<change_account>', methods = ['GET', 'POST'])
def manager_change_solution(change_account,account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			new_password = request.form.get('new_password')
			new_password_again = request.form.get('new_password_again')
			oringin_password = request.form.get('oringin_password')

			cur.execute("SELECT * FROM loginlist WHERE password='{oringin_password}'".format(oringin_password=oringin_password, ))
			check_password = cur.fetchall()

			if (new_password!=new_password_again ):
				error = '兩個密碼輸入不同！'
				form = PasswordForm()
				back_home = '管理者'
				return render_template('change_password_input.html', form=form, account=account, password=password, change_account=change_account, error=error, back_home=back_home, )
			elif (check_password==[]):
				error = '原密碼輸入錯誤！'
				form = PasswordForm()
				back_home = '管理者'
				return render_template('change_password_input.html', form=form, account=account, password=password, change_account=change_account, error=error, back_home=back_home,)
			else:
				cur.execute("UPDATE loginlist SET password='{new_password}' WHERE account='{change_account}'".format(new_password=new_password, change_account=change_account, ))
				conn.commit()
				back_home = '管理者'
				return render_template('change_success.html', account=account, password=password, change_account=change_account, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)






class EmailInputForm(FlaskForm):
	the_password = PasswordField('',validators=[DataRequired()],render_kw={'autofocus': True})
	new_email = StringField('',validators=[DataRequired()])
	new_email_again = StringField('',validators=[DataRequired()])


@app.route('/change/email/input/<account>/<password>/<change_account>', methods = ['GET', 'POST'])
def change_email_input(account,password,change_account):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = EmailInputForm()
			back_home = '管理者'
			return render_template('change_email_input.html', form=form, account=account, password=password, back_home=back_home, change_account=change_account, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/change/email/solution/<account>/<password>/<change_account>', methods = ['GET', 'POST'])
def change_email_solution(account,password,change_account):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			the_password = request.form.get('the_password')
			new_email = request.form.get('new_email')
			new_email_again = request.form.get('new_email_again')

			cur.execute("SELECT password FROM loginlist WHERE account='{change_account}'".format(change_account=change_account, ))
			ture_password = cur.fetchone()

			if (new_email!=new_email_again):
				error = '兩次信箱輸入不一致！'
				form = EmailInputForm()
				back_home = '管理者'
				return render_template('change_email_input.html', form=form, account=account, password=password, error=error, back_home=back_home, change_account=change_account, )
			elif (the_password!=ture_password[0]):
				error = '密碼輸入不正確！'
				form = EmailInputForm()
				back_home = '管理者'
				return render_template('change_email_input.html', form=form, account=account, password=password, error=error, back_home=back_home, change_account=change_account, )
			elif ('@' not in new_email):
				error = '輸入不為信箱'
				form = EmailInputForm()
				back_home = '管理者'
				return render_template('change_email_input.html', form=form, account=account, password=password, error=error, back_home=back_home, change_account=change_account, )
			else:
				cur.execute("UPDATE loginlist SET email='{new_email}'".format(new_email=new_email, ))
				conn.commit()

				cur.execute("SELECT email FROM loginlist WHERE account='{change_account}'".format(change_account=change_account, ))
				select_send_mail = cur.fetchone()
				send_mail = select_send_mail[0]

				msg = Message('更改信箱成功！', sender=app.config['MAIL_USERNAME'], recipients=[send_mail])
				msg.html = render_template('mail_change_body.html' )
				mail.send(msg)
				return render_template('mail_change_success.html', account=account, password=password, send_mail=send_mail, change_account=change_account, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


#-----------------------------------------------------------------------------------------------------------------
#更改成員資料

class CangePeoSearchForm(FlaskForm):
	peo_search = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

class CangePeoForm(FlaskForm):
	peo_input = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

@app.route('/change_people/search/<account>/<password>', methods = ['GET', 'POST'])
def change_peo_search(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = CangePeoSearchForm()
			back_home = '管理者'
			return render_template('change_peo_search.html', form=form, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = CangePeoSearchForm()
			back_home = '使用者'
			return render_template('change_peo_search.html', form=form, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/change_people/input/<account>/<password>', methods = ['GET', 'POST'])
def change_peo_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			peo_search = request.form.get('peo_search')

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id LIKE '%{peo_search}%' "
				"OR people_status LIKE '%{peo_search}%' OR people_class LIKE '%{peo_search}%' "
				"OR people_name LIKE '%{peo_search}%'".format(peo_search=peo_search, ))
			search_peo_sol = cur.fetchall()


			if (search_peo_sol==[]):
				error = '資料裡沒有{peo_search}的成員，請重新輸入'.format(peo_search=peo_search, )
				form = CangePeoSearchForm()
				back_home = '管理者'
				return render_template('change_peo_search.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else:
				form = CangePeoForm()
				back_home = '管理者'
				return render_template('change_peo_input.html', form=form, account=account, password=password, back_home=back_home, search_peo_sol=search_peo_sol, peo_search=peo_search, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			peo_search = request.form.get('peo_search')

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id LIKE '%{peo_search}%' "
				"OR people_status LIKE '%{peo_search}%' OR people_class LIKE '%{peo_search}%' "
				"OR people_name LIKE '%{peo_search}%'".format(peo_search=peo_search, ))
			search_peo_sol = cur.fetchall()

			if (search_peo_sol==[]):
				error = '資料裡沒有{peo_search}的成員，請重新輸入'.format(peo_search=peo_search, )
				form = CangePeoSearchForm()
				back_home = '使用者'
				return render_template('change_peo_search.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else:
				form = CangePeoForm()
				back_home = '使用者'
				return render_template('change_peo_input.html', form=form, account=account, password=password, back_home=back_home, search_peo_sol=search_peo_sol, peo_search=peo_search, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



class ChangePeoDetailForm(FlaskForm):
	#change_peo_id = StringField('', description=['編碼必須是五碼數字'],validators=[DataRequired()], render_kw={'autofocus': True})
	change_peo_status = SelectField('', choices=[('老師', '老師'),('學生', '學生'),('家長', '家長'),])
	change_peo_class = StringField('', validators=[DataRequired()])
	change_peo_name = StringField('',validators=[DataRequired()])

	#def __init__(self,input_choices,*args,**kwargs):
	#	super(TestBookForm,self).__init__(*args,**kwargs)
	#	self.test.choices = input_choices


@app.route('/change_people/detail/<account>/<password>/<peo_search>', methods = ['GET', 'POST'])
def change_peo_detail(account,password,peo_search):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			peo_input = request.form.get('peo_input')

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id='{peo_input}'".format(peo_input=peo_input, ))
			select_peo = cur.fetchone()

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id LIKE '%{peo_search}%' "
				"OR people_status LIKE '%{peo_search}%' OR people_class LIKE '%{peo_search}%' "
				"OR people_name LIKE '%{peo_search}%'".format(peo_search=peo_search, ))
			search_peo_sol = cur.fetchall()

			if (select_peo==None):
				error = '編碼輸入錯誤'
				form = CangePeoForm()
				back_home = '管理者'
				return render_template('change_peo_input.html', form=form, account=account, password=password, back_home=back_home, search_peo_sol=search_peo_sol, peo_search=peo_search, error=error, )

			else:
				form = ChangePeoDetailForm()
				#form.change_peo_id.default = (select_peo[0])
				form.change_peo_status.default = (select_peo[1])
				form.change_peo_class.default = (select_peo[2])
				form.change_peo_name.default = (select_peo[3])
				form.process()
				back_home = '管理者'
				return render_template('change_peo_detail.html', form=form, account=account, password=password, back_home=back_home, peo_input=peo_input, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			peo_input = request.form.get('peo_input')

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id='{peo_input}'".format(peo_input=peo_input, ))
			select_peo = cur.fetchone()

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id LIKE '%{peo_search}%' "
				"OR people_status LIKE '%{peo_search}%' OR people_class LIKE '%{peo_search}%' "
				"OR people_name LIKE '%{peo_search}%'".format(peo_search=peo_search, ))
			search_peo_sol = cur.fetchall()

			if (select_peo==None):
				error = '編碼輸入錯誤'
				form = CangePeoForm()
				back_home = '使用者'
				return render_template('change_peo_input.html', form=form, account=account, password=password, back_home=back_home, search_peo_sol=search_peo_sol, peo_search=peo_search, error=error, )

			else:
				form = ChangePeoDetailForm()
				#form.change_peo_id.default = (select_peo[0])
				form.change_peo_status.default = (select_peo[1])
				form.change_peo_class.default = (select_peo[2])
				form.change_peo_name.default = (select_peo[3])
				form.process()
				back_home = '使用者'
				return render_template('change_peo_detail.html', form=form, account=account, password=password, back_home=back_home, peo_input=peo_input, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)




@app.route('/change_people/solution/<account>/<password>/<peo_input>', methods = ['GET', 'POST'])
def change_peo_solution(account,password,peo_input):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			#peo_id_input = request.form.get('change_peo_id')
			peo_sta_input = request.form.get('change_peo_status')
			peo_cla_input = request.form.get('change_peo_class')
			peo_name_input = request.form.get('change_peo_name')

			cur.execute("SELECT people_id,people_name FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_input, ))
			select_peo = cur.fetchone()

			cur.execute("UPDATE peoplelist SET "
				"people_status='{peo_sta_input}', "
				"people_class='{peo_cla_input}', people_name='{peo_name_input}' "
				"WHERE people_id='{peo_input}'".format(peo_input=peo_input, peo_sta_input=peo_sta_input, peo_cla_input=peo_cla_input, peo_name_input=peo_name_input, ))
			conn.commit()

			cur.execute("SELECT * FROM peoplelist WHERE people_id='{peo_input}'".format(peo_input=peo_input, ))
			print_change_peo = cur.fetchone()
			back_home = '管理者'
			return render_template('change_peo_success.html', account=account, password=password, back_home=back_home, print_change_peo=print_change_peo, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

						#peo_id_input = request.form.get('change_peo_id')
			peo_sta_input = request.form.get('change_peo_status')
			peo_cla_input = request.form.get('change_peo_class')
			peo_name_input = request.form.get('change_peo_name')

			cur.execute("SELECT people_id,people_name FROM peoplelist WHERE people_id='{peo_id_input}'".format(peo_id_input=peo_input, ))
			select_peo = cur.fetchone()

			cur.execute("UPDATE peoplelist SET "
				"people_status='{peo_sta_input}', "
				"people_class='{peo_cla_input}', people_name='{peo_name_input}' "
				"WHERE people_id='{peo_input}'".format(peo_input=peo_input, peo_sta_input=peo_sta_input, peo_cla_input=peo_cla_input, peo_name_input=peo_name_input, ))
			conn.commit()

			cur.execute("SELECT * FROM peoplelist WHERE people_id='{peo_input}'".format(peo_input=peo_input, ))
			print_change_peo = cur.fetchone()
			back_home = '使用者'
			return render_template('change_peo_success.html', account=account, password=password, back_home=back_home, print_change_peo=print_change_peo, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)






#--------------------------------------------------------------------------------------------
#教具----trachaid

@app.route('/teachaid/search/input/<account>/<password>', methods = ['GET', 'POST'])
def search_teachaid_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = SearchForm()
			return render_template('search_teachaid_input.html',title = 'Search',form=form, account=account, password=password, )

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/teachaid/search/solution/<account>/<password>', methods = ['GET', 'POST'])
def search_teachaid_solution(account,password):

	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	key_word = request.form.get('key_word')

	cur.execute("SELECT teachaid_id, teachaid_name, teachaid_number, if_borrow FROM teachaid_list WHERE teachaid_id LIKE '%{keyword}%' OR teachaid_name LIKE '%{key}%' ORDER BY if_borrow, teachaid_id ASC".format(keyword=key_word,key=key_word ))
	search_teachaid = cur.fetchall()

	if (search_teachaid==[]):
		error = "我們找不到{key_word}".format(key_word=key_word)
		form = SearchForm()
		return render_template('search_teachaid_input.html',form=form, error=error, account=account, password=password, )

	else:
		return render_template(
			'search_teachaid_solution.html',
			search_teachaid=search_teachaid, account=account, password=password, back_home='管理者'
	)
		conn.close()














#---------------------------------------------------------------
#Borrow Teachaid

class Borrow_Peo_Form(FlaskForm):
	people_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

class Borrow_Teachaid_Form(FlaskForm):
	teachaid_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})


@app.route('/teachaid/borrow/peo/input/<account>/<password>', methods = ['GET', 'POST'])
def borrow_teachaid_peo(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = Borrow_Peo_Form()
			back_home = '管理者'
			return render_template('borrow_teachaid_peoid_input.html',form=form, account=account, password=password, back_home=back_home, peo_word='0', the_teachaid='0')
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/borrow/teachaid_id/input/<account>/<password>/<peo_word>/<the_teachaid>', methods = ['GET', 'POST'])
def borrow_teachaid(account,password,peo_word,the_teachaid):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			if (peo_word!='0'):
				borrow_peo_id = peo_word

				cur.execute("SELECT * FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
				b = cur.fetchone()

				if (b==None):
					form = Borrow_Peo_Form()
					back_home = '管理者'
					error='資料裡沒有{peo_id}這個成員'.format(peo_id=borrow_peo_id)
					borrow_peo_id = '0'
					the_teachaid = '0'
					return render_template('borrow_teachaid_peoid_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=borrow_peo_id,the_teachaid=the_teachaid, )

				else:
					cur.execute("SELECT teachaid_name FROM teachaid_list WHERE teachaid_id='{the_teachaid}'".format(the_teachaid=the_teachaid, ))
					the_teachaid_name = cur.fetchone()

					error = '{the_teachaid}--{the_teachaid_name}：借書成功！'.format(the_teachaid=the_teachaid, the_teachaid_name=the_teachaid_name[0], )


					cur.execute("SELECT id FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					peo_bor_teachaid_number = cur.fetchall()

					cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
					bor_peo_id, bor_peo_sta, bor_peo_class, bor_peo_name = cur.fetchone()

					cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_teachaid = cur.fetchall()

					form = Borrow_Teachaid_Form()
					back_home = '管理者'
					return render_template('borrow_teachaid_id_input.html', error=error, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_class, peo_name=bor_peo_name, print_bor_teachaid=print_bor_teachaid, peo_word=borrow_peo_id, account=account, password=password, back_home=back_home,  )

			else:

				borrow_peo_id = request.form.get('people_word')

				cur.execute("SELECT * FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
				b = cur.fetchone()

				if (b==None):
					form = Borrow_Peo_Form()
					back_home = '管理者'
					error='資料裡沒有{peo_id}這個成員'.format(peo_id=borrow_peo_id)
					borrow_peo_id = '0'
					the_teachaid = '0'
					return render_template('borrow_teachaid_peoid_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=borrow_peo_id, the_teachaid=the_teachaid, )

				else:
					cur.execute("SELECT id FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					peo_bor_teachaid_number = cur.fetchall()

					cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
					bor_peo_id, bor_peo_sta, bor_peo_class, bor_peo_name = cur.fetchone()

					cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_teachaid = cur.fetchall()

					form = Borrow_Teachaid_Form()
					back_home = '管理者'
					return render_template('borrow_teachaid_id_input.html',form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_class, peo_name=bor_peo_name, print_bor_teachaid=print_bor_teachaid, peo_word=borrow_peo_id, account=account, password=password, back_home=back_home,  )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)


	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/borrow/teachaid/solution/<account>/<password>', methods=['POST','GET'])
def borrow_teachaid_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			borrow_teachaid_id = request.form.get('teachaid_word')
			borrow_peo_id = request.form.get('peo_word')

			cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id = '{teachaid_id}'".format(teachaid_id=borrow_teachaid_id, ))
			a = cur.fetchone()

			cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
			print_bor_teachaid = cur.fetchall()

			cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id = '{peopleid}'".format(peopleid=borrow_peo_id, ))
			bor_peo_id, bor_peo_sta, bor_peo_cla, bor_peo_name = cur.fetchone()

			if (a==None):
				form = Borrow_Teachaid_Form()
				back_home = '管理者'
				error='資料裡沒有{teachaid_id}這本書'.format(teachaid_id=borrow_teachaid_id)
				return render_template('borrow_teachaid_solution.html',account=account,password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_teachaid=print_bor_teachaid, peo_word=borrow_peo_id, error=error, back_home=back_home, )


			else:
				cur.execute("SELECT teachaid_name, if_borrow, teachaid_number FROM teachaid_list WHERE teachaid_id = '{teachaid_id}'".format(teachaid_id=borrow_teachaid_id, ))
				bor_teachaid_name, bor_teachaid_ifborrow ,bor_teachaid_number= cur.fetchone()

				cur.execute("SELECT id FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
				bor_teachaid_num = len(cur.fetchall())

				cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
				print_bor_teachaid = cur.fetchall()

				if (bor_teachaid_ifborrow=='已借出'):
					form = Borrow_Teachaid_Form()
					back_home = '管理者'
					error='{teachaid_id}已被借出'.format(teachaid_id=borrow_teachaid_id)
					return render_template('borrow_teachaid_solution.html', account=account, password=password, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_teachaid=print_bor_teachaid, peo_word=borrow_peo_id, error=error, back_home=back_home, )

				elif (bor_teachaid_name==None):
					error = '未找到{borrow_teachaid_id}此本書'.format(borrow_teachaid_id=borrow_teachaid_id, )
					form = Borrow_Teachaid_Form()
					back_home = '管理者'
					return render_template('borrow_teachaid_solution.html', account=account, password=password, form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_teachaid=print_bor_teachaid, peo_word=borrow_peo_id, error=error, back_home=back_home, )

				elif (bor_peo_sta=='學生' or bor_peo_sta=='家長'):
					error='{peo_name}沒有權限借教具'.format(peo_name=bor_peo_name)
					form = Borrow_Peo_Form()
					back_home = '管理者'
					peo_word = '0'
					the_teachaid = '0'
					return render_template('borrow_teachaid_peoid_input.html', form=form, error=error, account=account, password=password, back_home=back_home, peo_word=peo_word, the_teachaid=the_teachaid, )

				else:
					time_now = datetime.datetime.now()
					bor_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )

					cur.execute(
						"UPDATE teachaid_list SET if_borrow='已借出',"
						"people_id='{peo_id}', borrow_status='{bor_sta}', "
						"borrow_class='{bor_cla}', "
						"people_name='{peo_name}', borrow_time='{bor_time}' "
						"WHERE teachaid_id='{teachaid_id}'".format(peo_id=bor_peo_id, bor_sta=bor_peo_sta, bor_cla=bor_peo_cla, peo_name=bor_peo_name, bor_time=bor_time, teachaid_id=borrow_teachaid_id, ))
					conn.commit()



					cur.execute("INSERT INTO teachaid_his (borrow_time,teachaid_id,teachaid_name, teachaid_number,if_borrow,people_id,people_status,people_class,people_name) "
							"VALUES ('{borrow_time}','{borrow_tea_id}','{bor_tea_name}', '{bor_teachaid_number}', "
							"'借出','{borrow_peo_id}','{bor_peo_sta}','{bor_peo_cla}', "
							"'{bor_peo_name}')".format(borrow_time=bor_time, borrow_tea_id=borrow_teachaid_id, bor_tea_name=bor_teachaid_name, borrow_peo_id=bor_peo_id, bor_peo_sta=bor_peo_sta, bor_peo_cla=bor_peo_cla, bor_peo_name=bor_peo_name, bor_teachaid_number=bor_teachaid_number, ))
					conn.commit()

					cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{peopleid}'".format(peopleid=borrow_peo_id))
					print_bor_teachaid = cur.fetchall()

					form = Borrow_Teachaid_Form()

					#print(form.validate_on_submit())

					if form.validate_on_submit():
						return redirect(url_for('borrow_teachaid', account=account, password=password, peo_word=borrow_peo_id, the_teachaid=borrow_teachaid_id, ))
					else:
						pass


					back_home = '管理者'
					return render_template('borrow_teachaid_solution.html', account=account, password=password,form=form, peo_id=bor_peo_id, peo_sta=bor_peo_sta, peo_class=bor_peo_cla, peo_name=bor_peo_name, print_bor_teachaid=print_bor_teachaid, peo_word=borrow_peo_id, back_home=back_home, )

				conn.close()
				conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)


	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)




#--------------------------------------------------------------------------
#Return Teachaid

class Return_Teachaid_Form(FlaskForm):
	teachaid_word = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})


@app.route('/return/teachaid_id/input/<account>/<password>', methods = ['GET', 'POST'])
def return_teachaid(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = Return_Teachaid_Form()
			back_home = '管理者'
			submit_empty = '0'
			the_teachaid = '0'
			return render_template('return_teachaid_id_input.html',form=form, account=account, password=password, back_home=back_home, submit_empty=submit_empty, the_teachaid=the_teachaid, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/return/teachaid/solution/<account>/<password>/<submit_empty>/<the_teachaid>', methods=['POST','GET'])
def return_teachaid_solution(account,password,submit_empty,the_teachaid):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			if (submit_empty!='0'):
				cur.execute("SELECT teachaid_name FROM teachaid_list WHERE teachaid_id='{the_teachaid}'".format(the_teachaid=the_teachaid, ))
				the_teachaid_name = cur.fetchone()

				error = '{the_teachaid}--{the_teachaid_name}：歸還成功！'.format(the_teachaid=the_teachaid, the_teachaid_name=the_teachaid_name[0], )
				form = Return_Teachaid_Form()
				back_home = '管理者'

				cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{ret_peo_id}'".format(ret_peo_id=submit_empty))
				print_ret_teachaid = cur.fetchall()

				cur.execute("SELECT people_id, people_status, people_class, people_name FROM peoplelist WHERE people_id='{ret_peo_id}'".format(ret_peo_id=submit_empty, ))
				ret_peo_id, ret_peo_sta, ret_peo_cla, ret_peo_name = cur.fetchone()

				submit_empty = '0'
				the_teachaid = '0'
				return render_template('return_teachaid_solution.html', error=error, form=form, peo_id=ret_peo_id, peo_sta=ret_peo_sta, peo_class=ret_peo_cla, peo_name=ret_peo_name, peo_word=ret_peo_id, account=account, password=password, back_home=back_home, print_ret_teachaid=print_ret_teachaid, submit_empty=submit_empty, the_teachaid=the_teachaid, )


			else:
				return_teachaid_id = request.form.get('teachaid_word')

				cur.execute("SELECT teachaid_name, if_borrow, people_id, borrow_status, borrow_class, people_name, borrow_time FROM teachaid_list WHERE teachaid_id = '{teachaid_id}'".format(teachaid_id=return_teachaid_id, ))
				a = cur.fetchone()

				if(a==None):
					error='資料裡沒有{teachaid_id}'.format(teachaid_id=return_teachaid_id)
					form = Return_Teachaid_Form()
					back_home = '管理者'
					submit_empty = '0'
					the_teachaid = '0'
					return render_template('return_teachaid_id_input.html',the_teachaid=the_teachaid, form=form, account=account, password=password, back_home=back_home, error=error, submit_empty=submit_empty, )

				else:
					cur.execute("SELECT teachaid_name, teachaid_number, if_borrow, people_id, borrow_status, borrow_class, people_name, borrow_time FROM teachaid_list WHERE teachaid_id = '{teachaid_id}'".format(teachaid_id=return_teachaid_id, ))
					ret_teachaid_name, ret_teachaid_number, ret_teachaid_ifborrow, ret_peo_id, ret_peo_sta, ret_peo_cla, ret_peo_name, bor_time = cur.fetchone()

					if (ret_teachaid_ifborrow=='未借出'):
						error='{teachaid_id}未被借出'.format(teachaid_id=return_teachaid_id)
						form = Return_Teachaid_Form()
						back_home = '管理者'
						submit_empty = '0'
						the_teachaid = '0'
						return render_template('return_teachaid_id_input.html', the_teachaid=the_teachaid, form=form, account=account, password=password, back_home=back_home, error=error, submit_empty=submit_empty )


					else:
						cur.execute("UPDATE teachaid_list SET if_borrow='未借出', people_id=Null, borrow_status=Null, borrow_class=Null, people_name=Null, borrow_time=Null WHERE teachaid_id='{teachaid_id}'".format( teachaid_id=return_teachaid_id, ))
						conn.commit()

						cur.execute("SELECT teachaid_id, teachaid_name, borrow_time FROM teachaid_list WHERE people_id='{ret_peo_id}'".format(ret_peo_id=ret_peo_id))
						print_ret_teachaid = cur.fetchall()

						time_now = datetime.datetime.now()
						ret_time = "{year_now}/{month_now:02d}/{day_now:02d}, {hour_now}時{minute_now}分{second_now}秒".format(year_now=time_now.year, month_now=time_now.month, day_now=time_now.day, hour_now=time_now.hour, minute_now=time_now.minute, second_now=time_now.second, )

						cur.execute("INSERT INTO teachaid_his (borrow_time,teachaid_id,teachaid_name, teachaid_number,if_borrow,people_id,people_status,people_class,people_name) "
							"VALUES ('{borrow_time}','{ret_tea_id}','{ret_tea_name}', '{ret_teachaid_number}', "
							"'還書','{ret_peo_id}','{ret_peo_sta}','{ret_peo_cla}', "
							"'{ret_peo_name}')".format(borrow_time=bor_time, ret_tea_id=return_teachaid_id, ret_tea_name=ret_teachaid_name, ret_teachaid_number=ret_teachaid_number, ret_peo_id=ret_peo_id, ret_peo_sta=ret_peo_sta, ret_peo_cla=ret_peo_cla, ret_peo_name=ret_peo_name, ))
						conn.commit()

						form = Return_Teachaid_Form()


						if form.validate_on_submit():
							return redirect(url_for('return_teachaid_solution',account=account,password=password, submit_empty=ret_peo_id, the_teachaid=return_teachaid_id, ))
							#傳送submit_empty是為了顯示出還書的人剩哪些書沒還
						else:
							pass

						back_home = '管理者'
						return render_template('return_teachaid_solution.html',form=form, peo_id=ret_peo_id, peo_sta=ret_peo_sta, peo_class=ret_peo_cla, peo_name=ret_peo_name, peo_word=ret_peo_id, account=account, password=password, back_home=back_home, print_ret_teachaid=print_ret_teachaid, )


				conn.close()
				conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)


	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)
























#------------------------------------------------------------------
#Unreturn Unreturn

class Unreturn_Teachaid_Form(FlaskForm):
	key_word = StringField('', description=['可輸入教具編碼、教具名、成員編碼、成員姓名、成員班級、成員身份等關鍵字。'],validators=[DataRequired()],render_kw={'autofocus': True}, )
	keyword_or_all = SelectField('', choices=[('keyword', '關鍵字'),('all', '全部相同'),])


@app.route('/unreturn/teachaid/<account>/<password>', methods = ['GET', 'POST'])
def unreturn_teachaid(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = Unreturn_Teachaid_Form()
			back_home = '管理者'
			return render_template('unreturn_teachaid_input.html', form=form, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/unreturn/teachaid/solution/<account>/<password>', methods=['GET', 'POST'])
def unreturn_teachaid_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			key_word = request.form.get('key_word')
			keyword_or_all = request.form.get('keyword_or_all')

			if (keyword_or_all=='keyword'):
				cur.execute(
					"SELECT * "
					"FROM teachaid_list "
					"WHERE if_borrow='已借出' AND (teachaid_name LIKE '%{keyword}%' "
					"OR teachaid_id LIKE '%{keyword}%' OR people_id LIKE '%{keyword}%'"
					"OR people_name LIKE '%{keyword}%' OR borrow_class LIKE '%{keyword}%'"
					"OR borrow_status LIKE '%{keyword}%') ORDER BY borrow_class, people_name DESC".format(keyword=key_word, ))

				unreturn_teachaid = cur.fetchall()

			else:
				cur.execute("SELECT * FROM teachaid_list "
					"WHERE if_borrow='已借出' AND (teachaid_name='{keyword}' "
					"OR teachaid_id='{keyword}' OR people_id='{keyword}' "
					"OR people_name='{keyword}' OR borrow_class='{keyword}' "
					"OR borrow_status='{keyword}') ORDER BY borrow_class, people_name DESC".format(keyword=key_word, ))
				unreturn_teachaid = cur.fetchall()

			if (unreturn_teachaid==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = Unreturn_Teachaid_Form()
				back_home = '管理者'
				return render_template('unreturn_teachaid_input.html',form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				back_home = '管理者'
				return render_template('unreturn_teachaid_solution.html',unreturn_teachaid=unreturn_teachaid,account=account, password=password, back_home=back_home, )

			conn.close()

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)


	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/unreturn_all/teachaid/<account>/<password>', methods=['GET', 'POST'])
def unreturn_all_teachaid(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM teachaid_list WHERE if_borrow='已借出' ORDER BY borrow_class, people_name DESC")
			all_unreturn_teachaid = cur.fetchall()
			back_home = '管理者'
			return render_template('unreturn_teachaid_solution.html',unreturn_teachaid=all_unreturn_teachaid,account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



#------------------------------------------------------------------------------------------------------------------
#manager_teachaid


@app.route('/manager_teachaid/choose/<account>/<password>')
def teachaid_choose(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			back_home = '管理者'
			return render_template('teachaid/teachaid_choose.html', account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			back_home = '使用者'
			return render_template('teachaid/teachaid_choose.html', account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/all_teachaid/<account>/<password>', methods = ['GET', 'POST'])
def all_tea(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			#cur.execute("SELECT * FROM teachaid_list WHERE id!='1' ORDER BY book_id ASC")
			cur.execute("SELECT teachaid_id, teachaid_name, teachaid_number, if_borrow FROM teachaid_list WHERE id!='1' ORDER BY teachaid_id ASC")
			search_teachaid = cur.fetchall()
			back_home = '管理者'
			return render_template('search_teachaid_solution.html',account=account,password=password, search_teachaid=search_teachaid, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)




class InsertTeaForm(FlaskForm):
	insert_tea_id = StringField('', description=['編碼開頭必須為 T，後面加上五碼數字'], validators=[DataRequired()], render_kw={'autofocus': True})
	insert_tea_name = StringField('',validators=[DataRequired()])
	insert_tea_number = StringField('',validators=[DataRequired()])


@app.route('/insert_teachaid/input/<account>/<password>', methods = ['GET', 'POST'])
def insert_tea_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			form = InsertTeaForm()
			back_home = '管理者'
			return render_template('teachaid/insert_tea_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			form = InsertTeaForm()
			back_home = '使用者'
			return render_template('teachaid/insert_tea_input.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/insert_teachaid/solution/<account>/<password>', methods = ['GET', 'POST'])
def insert_tea_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			tea_id_input = request.form.get('insert_tea_id')
			tea_name_input = request.form.get('insert_tea_name')
			tea_number_input = request.form.get('insert_tea_number')

			cur.execute("SELECT teachaid_id,teachaid_name FROM teachaid_list WHERE teachaid_id='{tea_id_input}'".format(tea_id_input=tea_id_input, ))
			select_tea = cur.fetchone()

			#str.isdigit 是檢查字串是否為數字
			if (tea_id_input[0]!='T' or len(tea_id_input)!=6 or str.isdigit(tea_id_input[1:])!=1):
				error = '書目編碼輸入錯誤！書目編碼需為6碼，且第1碼需為T後五碼需為數字！'.format(tea_id_input=tea_id_input)
				form = InsertTeaForm()
				back_home = '管理者'
				return render_template('teachaid/insert_tea_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			elif (select_tea!=None):
				error = '{tea_id_input}已有書名'.format(tea_id_input=tea_id_input)
				form = InsertTeaForm()
				back_home = '管理者'
				return render_template('teachaid/insert_tea_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else :
				cur.execute("INSERT INTO teachaid_list (teachaid_id,teachaid_name,if_borrow,teachaid_number) VALUES ('{tea_id_input}','{tea_name_input}','未借出','{tea_number_input}')".format(tea_id_input=tea_id_input, tea_name_input=tea_name_input, tea_number_input=tea_number_input, ))
				conn.commit()

				cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id='{tea_id_input}'".format(tea_id_input=tea_id_input, ))
				print_insert_tea = cur.fetchone()
				back_home = '管理者'
				return render_template('teachaid/insert_tea_success.html',print_insert_tea=print_insert_tea, account=account, password=password, back_home=back_home, )


		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			tea_id_input = request.form.get('insert_tea_id')
			tea_name_input = request.form.get('insert_tea_name')
			tea_number_input = request.form.get('insert_tea_number')

			cur.execute("SELECT teachaid_id,teachaid_name FROM teachaid_list WHERE teachaid_id='{tea_id_input}'".format(tea_id_input=tea_id_input, ))
			select_tea = cur.fetchone()

			#str.isdigit 是檢查字串是否為數字
			if (tea_id_input[0]!='T' or len(tea_id_input)!=6 or str.isdigit(tea_id_input[1:])!=1):
				error = '書目編碼輸入錯誤！書目編碼需為6碼，且第1碼需為T後五碼需為數字！'.format(tea_id_input=tea_id_input)
				form = InsertTeaForm()
				back_home = '使用者'
				return render_template('teachaid/insert_tea_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			elif (select_tea!=None):
				error = '{tea_id_input}已有書名'.format(tea_id_input=tea_id_input)
				form = InsertTeaForm()
				back_home = '使用者'
				return render_template('teachaid/insert_tea_input.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else :
				cur.execute("INSERT INTO teachaid_list (teachaid_id,teachaid_name,if_borrow,teachaid_number) VALUES ('{tea_id_input}','{tea_name_input}','未借出','{tea_number_input}')".format(tea_id_input=tea_id_input, tea_name_input=tea_name_input, tea_number_input=tea_number_input, ))
				conn.commit()

				cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id='{tea_id_input}'".format(tea_id_input=tea_id_input, ))
				print_insert_tea = cur.fetchone()
				back_home = '使用者'
				return render_template('teachaid/insert_tea_success.html',print_insert_tea=print_insert_tea, account=account, password=password, back_home=back_home, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


#class ManageTeaForm(FlaskForm):
#	account = StringField('',validators=[DataRequired()], render_kw={'autofocus': True})
#	password = StringField('',validators=[DataRequired()])




class DeleteTea_Search_Form(FlaskForm):
	key_word = StringField('',validators=[DataRequired()], render_kw={'autofocus': True}, )

@app.route('/delete_teachaid/search/<account>/<password>', methods = ['GET', 'POST'])
def delete_tea_search(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = DeleteTea_Search_Form()
			back_home = '管理者'
			return render_template('teachaid/delete_tea_search.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):
			form = DeleteTea_Search_Form()
			back_home = '使用者'
			return render_template('teachaid/delete_tea_search.html', form=form, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)

class DeleteTea_Input_Form(FlaskForm):
	tea_id_input = StringField('', validators=[DataRequired()], render_kw={'autofocus': True}, )

@app.route('/delete_teachaid/input/<account>/<password>', methods = ['GET', 'POST'])
def delete_tea_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			key_word = request.form.get('key_word')

			cur.execute(
				"SELECT teachaid_id, teachaid_name, if_borrow, teachaid_number,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM teachaid_list "
				"WHERE teachaid_name LIKE '%{keyword}%' "
				"OR teachaid_id LIKE '%{keyword}%' OR teachaid_number LIKE '%{keyword}%' ORDER BY teachaid_id ASC".format(keyword=key_word, ))

			search_tea = cur.fetchall()

			if (search_tea==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = DeleteTea_Search_Form()
				back_home = '管理者'
				return render_template('teachaid/delete_tea_search.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				form = DeleteTea_Input_Form()
				back_home = '管理者'
				return render_template('teachaid/delete_tea_input.html', form=form, search_tea=search_tea, key_word=key_word, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			key_word = request.form.get('key_word')

			cur.execute(
				"SELECT teachaid_id, teachaid_name, if_borrow, teachaid_number,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM teachaid_list "
				"WHERE teachaid_name LIKE '%{keyword}%' "
				"OR teachaid_id LIKE '%{keyword}%' OR teachaid_number LIKE '%{keyword}%' ORDER BY teachaid_id ASC".format(keyword=key_word, ))

			search_tea = cur.fetchall()

			if (search_tea==[]):
				error = "我們找不到{key_word}".format(key_word=key_word)
				form = DeleteTea_Search_Form()
				back_home = '使用者'
				return render_template('teachaid/delete_tea_search.html', form=form, error=error, account=account, password=password, back_home=back_home, )

			else:
				form = DeleteTea_Input_Form()
				back_home = '使用者'
				return render_template('teachaid/delete_tea_input.html', form=form, search_tea=search_tea, key_word=key_word, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/delete_teachaid/sure/<account>/<password>/<key_word>', methods = ['GET', 'POST'])
def delete_tea_sure(account,password,key_word):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			tea_id_input = request.form.get('tea_id_input')

			cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id='{tea_id_input}'".format(tea_id_input=tea_id_input))
			select_delete_tea = cur.fetchone()

			cur.execute(
				"SELECT teachaid_id, teachaid_name, if_borrow,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM teachaid_list "
				"WHERE teachaid_name LIKE '%{keyword}%' "
				"OR teachaid_id LIKE '%{keyword}%' OR teachaid_number LIKE '%{keyword}%'".format(keyword=key_word, ))
			search_tea = cur.fetchall()

			if (select_delete_tea==None):
				form = DeleteTea_Input_Form()
				back_home = '管理者'
				error = '資料裡沒有{tea_id_input}這本書'.format(tea_id_input=tea_id_input, )
				return render_template('teachaid/delete_tea_input.html', form=form, search_tea=search_tea, account=account, password=password, back_home=back_home, error=error, key_word=key_word, )

			else:
				select_tea_id = select_delete_tea[1]
				back_home = '管理者'
				return render_template('teachaid/delete_tea_sure.html', select_delete_tea=select_delete_tea, select_tea_id=select_tea_id, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			tea_id_input = request.form.get('tea_id_input')

			cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id='{tea_id_input}'".format(tea_id_input=tea_id_input))
			select_delete_tea = cur.fetchone()

			cur.execute(
				"SELECT teachaid_id, teachaid_name, if_borrow,"
				"people_id, borrow_status, borrow_class, "
				"people_name, borrow_time "
				"FROM teachaid_list "
				"WHERE teachaid_name LIKE '%{keyword}%' "
				"OR teachaid_id LIKE '%{keyword}%' teachaid_number LIKE '%{keyword}%'".format(keyword=key_word, ))
			search_tea = cur.fetchall()

			if (select_delete_tea==None):
				form = DeleteTea_Input_Form()
				back_home = '使用者'
				error = '資料裡沒有{tea_id_input}這本書'.format(tea_id_input=tea_id_input, )
				return render_template('teachaid/delete_tea_input.html', form=form, search_tea=search_tea, account=account, password=password, back_home=back_home, error=error, key_word=key_word, )

			else:
				select_tea_id = select_delete_tea[1]
				back_home = '使用者'
				return render_template('teachaid/delete_tea_sure.html', select_delete_tea=select_delete_tea, select_tea_id=select_tea_id, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/delete_teachaid/solution/<account>/<password>/<select_tea_id>', methods = ['GET', 'POST'])
def delete_tea_solution(account,password,select_tea_id):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id='{select_tea_id}'".format(select_tea_id=select_tea_id, ))
			select_tea = cur.fetchone()

			cur.execute("DELETE FROM teachaid_list "
				"WHERE teachaid_id='{select_tea_id}'".format(select_tea_id=select_tea_id, ))
			conn.commit()
			back_home = '管理者'
			return render_template('teachaid/delete_tea_success.html', select_tea=select_tea, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)


	elif (account==user_account):
		check_user = check_password_hash(password,user_password)
		if (check_user==1):

			cur.execute("SELECT * FROM teachaid_list WHERE teachaid_id='{select_tea_id}'".format(select_tea_id=select_tea_id, ))
			select_book = cur.fetchone()

			cur.execute("DELETE FROM teachaid_list "
				"WHERE teachaid_id='{select_tea_id}'".format(select_tea_id=select_tea_id, ))
			conn.commit()
			back_home = '使用者'
			return render_template('teachaid/delete_tea_success.html', select_tea=select_tea, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



class HistoryTea_Search_Form(FlaskForm):
	tea_input = StringField('',validators=[DataRequired()], render_kw={'autofocus': True}, )

@app.route('/teachaid/history_input/<account>/<password>', methods=['GET', 'POST'])
def teachaid_his_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			form = HistoryTea_Search_Form()

			back_home = '管理者'
			return render_template('teachaid/history_tea_input.html',account=account, password=password, back_home=back_home, form=form)

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/teachaid/history_soultion/<account>/<password>', methods = ['GET', 'POST'])
def history_tea_solution(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			tea_id_input = request.form.get('tea_input')

			cur.execute("SELECT * FROM teachaid_his WHERE teachaid_id='{tea_id}' AND if_borrow='借出'".format(tea_id=tea_id_input))
			select_history = cur.fetchall()

			if (select_history==[]):
				error = '我們找不到教具編碼為{tea_id}歷史紀錄。'.format(tea_id=tea_id_input, )
				form = HistoryTea_Search_Form()
				back_home = '管理者'
				return render_template('teachaid/history_tea_input.html', form=form, account=account, password=password, error=error, back_home=back_home, )
			else:
				select_tea = select_history[0]
				back_home = '管理者'
				return render_template('teachaid/history_tea_solution.html', select_tea=select_tea, select_history=select_history, account=account, password=password, back_home=back_home, )
		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/teachaid/all_history/<account>/<password>', methods=['GET', 'POST'])
def teachaid_history(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			cur.execute("SELECT * FROM teachaid_his")
			all_history = cur.fetchall()

			back_home = '管理者'
			return render_template('teachaid_history.html',account=account, password=password, back_home=back_home, all_history=all_history)

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)












#--------------------------------------------------------------------------------------------------------------
#以下尚未開放或完成


#photos = UploadSet('photos', IMAGES)

#app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
#configure_uploads(app, photos)


class CangeTeaSearchForm(FlaskForm):
	teachaid_search = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})

class CangeTeaForm(FlaskForm):
	teachaid_input = StringField('',validators=[DataRequired()],render_kw={'autofocus': True})


@app.route('/teachaid/image/search/<account>/<password>', methods=['GET', 'POST'])
def teachaid_image_search(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			form = CangeTeaSearchForm()
			back_home = '管理者'
			return render_template('teachaid_image_search.html',account=account, password=password, back_home=back_home, form=form)

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)


@app.route('/teachaid/image/input/<account>/<password>', methods = ['GET', 'POST'])
def teachaid_image_input(account,password):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			tea_search = request.form.get('teachaid_search')

			cur.execute("SELECT teachaid_id, teachaid_name, teachaid_number, teachaid_image FROM teachaid_list WHERE teachaid_id LIKE '%{tea_search}%' "
			"OR teachaid_name LIKE '%{tea_search}%' OR teachaid_number LIKE '%{tea_search}%' ".format(tea_search=tea_search, ))
			search_tea_sol = cur.fetchall()

			data_file = 'static/img'

			if (search_tea_sol==[]):
				error = '資料裡沒有{tea_search}的教具，請重新輸入'.format(tea_search=tea_search, )
				form = CangeTeaSearchForm()
				back_home = '管理者'
				return render_template('teachaid_image_search.html', form=form, account=account, password=password, back_home=back_home, error=error, )

			else:

				form = CangeTeaForm()
				back_home = '管理者'
				return render_template('teachaid_image_input.html', form=form, account=account, password=password, back_home=back_home, search_tea_sol=search_tea_sol, tea_search=tea_search, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)
	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)





@app.route('/teachaid/image/upload/<account>/<password>/<tea_search>', methods = ['GET', 'POST'])
def teachaid_image_upload(account,password,tea_search):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):

			teachaid_input = request.form.get('teachaid_input')

			cur.execute("SELECT teachaid_id, teachaid_name, teachaid_number, teachaid_image FROM teachaid_list WHERE teachaid_id='{tea_input}'".format(tea_input=teachaid_input, ))
			select_tea = cur.fetchone()
			print(select_tea)

			cur.execute("SELECT teachaid_id, teachaid_name, teachaid_number, teachaid_image FROM teachaid_list WHERE teachaid_id LIKE '%{tea_search}%' "
			"OR teachaid_name LIKE '%{tea_search}%' OR teachaid_number LIKE '%{tea_search}%' ".format(tea_search=tea_search, ))
			search_tea_sol = cur.fetchall()

			if (select_tea==None):
				error = '編碼輸入錯誤'
				form = CangeTeaForm()
				back_home = '管理者'
				return render_template('teachaid_image_input.html', form=form, account=account, password=password, back_home=back_home, search_tea_sol=search_tea_sol, tea_search=tea_search, error=error, )

			else:
				back_home = '管理者'
				return render_template('teachaid_image_upload.html', account=account, password=password, back_home=back_home, select_tea=select_tea, teachaid_input=teachaid_input, tea_search=tea_search, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)



@app.route('/teachaid/image/upload/success/<account>/<password>/<teachaid_input>/<tea_search>', methods = ['GET', 'POST'])
def teachaid_image_success(account,password,teachaid_input,tea_search):
	conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
	cur = conn.cursor()

	cur.execute("SELECT account, password FROM loginlist WHERE id='1' ")
	manager_detail = cur.fetchone()

	cur.execute("SELECT account, password FROM loginlist WHERE id='2' ")
	user_detail = cur.fetchone()

	manager_account = manager_detail[0]
	manager_password = manager_detail[1]

	user_account = user_detail[0]
	user_password = user_detail[1]

	if (account==manager_account):
		check_manager = check_password_hash(password,manager_password)
		if (check_manager==1):
			tea_image = request.files['photo']
			plt.show(tea_image)
			#print(type(tea_image))
			#tea_image = transform.rescale(tea_image, 0.1)
			tea_image_name = photos.save(tea_image)

			cur.execute("UPDATE teachaid_list SET teachaid_image='{tea_image}' WHERE teachaid_id='{teachaid_input}'".format(tea_image=tea_image_name, teachaid_input=teachaid_input, ))
			conn.commit()

			cur.execute("SELECT teachaid_id, teachaid_name, teachaid_number, teachaid_image FROM teachaid_list WHERE teachaid_id='{tea_input}'".format(tea_input=teachaid_input, ))
			select_tea = cur.fetchone()
			back_home = '管理者'

			return render_template('teachaid_image_success.html', account=account, password=password, back_home=back_home, select_tea=select_tea, tea_image=tea_image, )

		else:
			back_to_library_home = url_for('library')
			return redirect(back_to_library_home)

	else:
		back_to_library_home = url_for('library')
		return redirect(back_to_library_home)

#image = Image.open('File.jpg')
#image.show()
			#		tea_image = Image.open(data_file+search_tea_sol[3])
			#		search_tea_sol[3] = image.show()


@app.route('/upload', methods=['GET', 'POST'])
def upload():
	return render_template('upload.html')



@app.route('/upload/success', methods=['GET', 'POST'])
def upload_success():
	tea_image = request.files['photo']
	tea_image_name = photos.save(tea_image)
	#image_name = image.filename
	return tea_image_name














if __name__ == "__main__":
    app.run(debug=True)


