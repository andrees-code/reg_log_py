from flask import Flask, request, redirect, url_for, render_template, Blueprint, flash, session
import os
from dotenv import load_dotenv
import mysql.connector
import hashlib


auth  = Blueprint('auth', __name__, url_prefix='/auth')
load_dotenv()

conexion = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = os.getenv('BD_PASSWORD'),
    database = 'numero5'
)

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        passwd = request.form.get('passwd')
        if email and passwd:
            if len(passwd) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
                return redirect(url_for('auth.login'))
            if len(passwd) >= 6:
                try:
                    hash_passwd = hashlib.sha256(passwd.encode('UTF-8')).hexdigest()
                    cursor = conexion.cursor(dictionary=True)
                    cursor.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
                    user = cursor.fetchone()
                    if user:
                        if email == user['email'] and hash_passwd == user['passwd']:
                            flash('Usuario loggeado', 'success')
                            session['logged_in'] = True
                            session['email'] = user['email']
                            session['name'] = user['nombre']
                            return redirect(url_for('index'))
                        flash('email o contraseña incorrectos')
                        return redirect(url_for('auth.login'))
                    flash('Este usuario no existe', 'danger')
                    return redirect(url_for('auth.login'))
                        
                except Exception as e:
                    print(e)
                finally:
                    if cursor:
                        cursor.close()
                
        if not email or not passwd:
            flash('Completa todos los campos.', 'danger')
            return redirect(url_for('auth.login'))
                
    return render_template('login.html', title='LOGIN')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        passwd = request.form.get('passwd')
        
        if name and email and passwd:
            if len(passwd) < 6:
                flash('La contraseña de tener al meno 6 caracteres.', 'danger')
                return redirect(url_for('auth.register'))
            if len(passwd) >= 6:
                try:
                    hash_passwd = hashlib.sha256(passwd.encode('UTF-8')).hexdigest()
                    cursor = conexion.cursor(dictionary=True)
                    cursor.execute('SELECT email FROM usuarios WHERE email = %s', (email, ))
                    usuario = cursor.fetchone()
                    if usuario:
                        flash('Email ya registrado', 'danger')
                        return redirect(url_for('auth.register'))
                    
                    cursor.execute('INSERT INTO usuarios (nombre, email, passwd) VALUES (%s,%s,%s)',(name,email,hash_passwd))
                    conexion.commit()
                    cursor.execute('SELECT id FROM usuarios WHERE email = %s', (email, ))
                    user_id = cursor.fetchone()
                    session['user_id']= user_id['id']
                    session['email'] = email
                    session['logged_in'] = True
                    return redirect(url_for('index'))
                        
                except Exception as e:
                    print(e)
                finally:
                    if cursor:
                        cursor.close()
        if not name or not email or not passwd:
            flash('Completa todos los campos.', 'danger')
            return redirect(url_for('auth.register'))
            
    return render_template('register.html', title='REGISTER')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

