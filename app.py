import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey123")

cursos = [
    {
        "nombre": "Educacion",
        "descripcion_corta": "Curso educativo de ejemplo",
        "descripcion_larga": "Este curso desarrolla habilidades y conocimientos para todos.",
        "duracion": "3 meses",
        "modalidad": "Presencial",
        "edad_recomendada": "6-12 años",
        "fecha_inicio": "01/11/2025",
        "categoria": "General",
        "imagen": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "nombre": "Matematica",
        "descripcion_corta": "Curso de matemáticas divertidas",
        "descripcion_larga": "Aprende matemáticas de forma práctica y divertida.",
        "duracion": "2 meses",
        "modalidad": "Presencial",
        "edad_recomendada": "8-14 años",
        "fecha_inicio": "05/11/2025",
        "categoria": "Ciencias",
        "imagen": "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80"
    },
    {
        "nombre": "Ciencias",
        "descripcion_corta": "Curso de ciencias experimentales",
        "descripcion_larga": "Experimenta y aprende sobre el mundo que te rodea.",
        "duracion": "3 meses",
        "modalidad": "Presencial",
        "edad_recomendada": "7-13 años",
        "fecha_inicio": "10/11/2025",
        "categoria": "Ciencias",
        "imagen": "https://images.unsplash.com/photo-1646956141590-9503c35a27cf?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTl8fGNpZW5jaWFzfGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=500"

       
    },
    {
        "nombre": "Progamar",
        "descripcion_corta": "Curso creativo de programación para principiantes",
        "descripcion_larga": "Explora tu creatividad con técnicas programación.",
        "duracion": "2 meses",
        "modalidad": "Presencial",
        "edad_recomendada": "6-50 años",
        "fecha_inicio": "15/11/2025",
        "categoria": "Arte",
        "imagen": "https://images.unsplash.com/photo-1529101091764-c3526daf38fe?auto=format&fit=crop&w=800&q=80"
    }
]

SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 0)) if os.environ.get("SMTP_PORT") else None
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
CONTACT_RECIPIENT = os.environ.get("CONTACT_RECIPIENT", SMTP_USER)  # receptor por defecto

# Validación básica de email
EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")

# -----------------------------
# Rutas
# -----------------------------
@app.route('/')
def index():
    destacados = cursos[:3]
    return render_template('index.html', cursos=cursos, destacados=destacados)

@app.route('/cursos')
def todos_cursos():
    categoria = request.args.get('categoria', None)
    if categoria:
        filtrados = [c for c in cursos if c['categoria'].lower() == categoria.lower()]
    else:
        filtrados = cursos
    return render_template('courses.html', cursos=filtrados, categoria=categoria)

@app.route('/curso/<nombre>')
def curso(nombre):
    curso_obj = next((c for c in cursos if c["nombre"].lower() == nombre.lower()), None)
    if not curso_obj:
        return render_template('404.html'), 404
    return render_template('course.html', curso=curso_obj)

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('q', '').lower()
    resultados = [c for c in cursos if query in c['nombre'].lower() or query in c['descripcion_corta'].lower()]
    return render_template('buscar.html', query=query, resultados=resultados)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        mensaje = request.form.get('mensaje', '').strip()

        # Validaciones simples
        if not nombre or not email or not mensaje:
            flash("Por favor completa todos los campos.", "error")
            return redirect(url_for('contacto'))
        if not EMAIL_RE.match(email):
            flash("Por favor ingresa un email válido.", "error")
            return redirect(url_for('contacto'))

        # Intentar enviar correo (si está configurado)
        subject = f"Nuevo mensaje de contacto - {nombre}"
        body = f"Nombre: {nombre}\nEmail: {email}\n\nMensaje:\n{mensaje}"

        if SMTP_SERVER and SMTP_PORT and SMTP_USER and SMTP_PASSWORD and CONTACT_RECIPIENT:
            try:
                msg = EmailMessage()
                msg["From"] = SMTP_USER
                msg["To"] = CONTACT_RECIPIENT
                msg["Subject"] = subject
                msg.set_content(body)

                # Usar SSL si puerto 465, si no intentar STARTTLS
                if SMTP_PORT == 465:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                        server.ehlo()
                        if server.has_extn('STARTTLS'):
                            server.starttls(context=ssl.create_default_context())
                            server.ehlo()
                        server.login(SMTP_USER, SMTP_PASSWORD)
                        server.send_message(msg)

                flash(f"Gracias {nombre}, tu mensaje fue enviado correctamente.", "success")
            except Exception as e:
                # Si falla, mostrar mensaje amable y loggear en consola (o en archivo si prefieres)
                print("Error enviando correo:", e)
                flash("Hubo un problema al enviar tu mensaje. Intentaremos contactarte pronto.", "error")
        else:
            # Si no hay SMTP configurado, solo hacer flash (y podrías registrar en DB)
            print("Contacto (no enviado por email) - Nombre:", nombre, "Email:", email, "Mensaje:", mensaje)
            flash(f"Gracias {nombre}, tu mensaje fue recibido (modo prueba).", "success")

        return redirect(url_for('contacto'))

    return render_template('contact.html')

# -----------------------------
# Error handlers (opcionales)
# -----------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# -----------------------------
# Ejecutar app
# -----------------------------
if __name__ == '__main__':
    # En desarrollo es conveniente debug=True, en producción pasarlo por variable de entorno
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)
