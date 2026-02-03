import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template, session, flash
import requests
from routes.auth import auth
import mysql.connector

app = Flask(__name__)
app.register_blueprint(auth)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY_APP')

# Conexión a la base de datos
conexion = mysql.connector.connect(
    host='localhost',
    user='root',
    password=os.getenv('BD_PASSWORD'),
    database= 'numero5'
)

# ------------------ Ruta principal ------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    user_email = session.get('email')
    if not user_email:
        flash('No se encontró el usuario en sesión.', 'danger')
        return redirect(url_for('auth.login'))

    # Obtener personajes de la API
    response = requests.get('https://rickandmortyapi.com/api/character')
    characters = response.json().get('results', [])

    # Obtener favoritos del usuario
    favoritos = []
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True, buffered=True)
        cursor.execute('SELECT char_id FROM favoritos WHERE user_email = %s', (user_email,))
        favoritos_db = cursor.fetchall()
        favoritos = [f['char_id'] for f in favoritos_db]  # lista de char_id para saber cuáles ya son favoritos
    except Exception as e:
        print(e)
    finally:
        if cursor:
            cursor.close()

    # POST para añadir un favorito
    if request.method == 'POST':
        char_id = request.form.get('char_id')
        char_name = request.form.get('char_name')
        char_img = request.form.get('char_img')

        if char_id and char_name and char_img:
            # Verificar si ya está en favoritos
            cursor = None
            try:
                cursor = conexion.cursor(dictionary=True, buffered=True)
                cursor.execute(
                    'SELECT char_id FROM favoritos WHERE char_id = %s AND user_email = %s',
                    (char_id, user_email)
                )
                if cursor.fetchone():
                    flash('Ese personaje ya lo tienes en favoritos.', 'danger')
                else:
                    # Insertar en favoritos
                    cursor.execute(
                        'INSERT INTO favoritos (char_id, char_name, char_img, user_email) VALUES (%s, %s, %s, %s)',
                        (char_id, char_name, char_img, user_email)
                    )
                    conexion.commit()
                    flash('Personaje añadido a favoritos.', 'success')
            except Exception as e:
                print(e)
                flash('Error al añadir favorito.', 'danger')
            finally:
                if cursor:
                    cursor.close()
        return redirect(url_for('index'))  # Evitar resubmit

    return render_template('index.html', title='home', characters=characters, favoritos=favoritos)


# ------------------ Ruta favoritos ------------------
@app.route('/favoritos', methods=['GET', 'POST'])
def favoritos():
    user_email = session.get('email')
    if not session.get('logged_in') or not user_email:
        return redirect(url_for('auth.login'))

    # POST para eliminar favorito
    if request.method == 'POST':
        char_id = request.form.get('char_id')
        if char_id:
            cursor = None
            try:
                cursor = conexion.cursor(buffered=True)
                cursor.execute(
                    'DELETE FROM favoritos WHERE char_id = %s AND user_email = %s',
                    (char_id, user_email)
                )
                conexion.commit()
                flash('Personaje eliminado correctamente.', 'info')
            except Exception as e:
                print(e)
                flash('Error al eliminar favorito.', 'danger')
            finally:
                if cursor:
                    cursor.close()
        return redirect(url_for('favoritos'))

    # GET para mostrar favoritos
    favoritos_list = []
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True, buffered=True)
        cursor.execute('SELECT * FROM favoritos WHERE user_email = %s', (user_email,))
        favoritos_list = cursor.fetchall()
        if not favoritos_list:
            flash('No tienes favoritos añadidos.')
    except Exception as e:
        print(e)
        flash('Error al cargar favoritos.', 'danger')
    finally:
        if cursor:
            cursor.close()

    return render_template('favoritos.html', title='Favoritos', favoritos=favoritos_list)


# ------------------ Run app ------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
