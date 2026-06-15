from flask import Flask, render_template, request, jsonify, from flask import Flask, render_template, request, jsonify, send_file
import os
import csv
from datetime import datetime

app = Flask(__name__)

# Crear carpeta para los justificantes si no existe
CARPETA_DOCS = os.path.join(os.getcwd(), 'Justificantes_Alumnos')
if not os.path.exists(CARPETA_DOCS):
    os.makedirs(CARPETA_DOCS)

app.config['UPLOAD_FOLDER'] = CARPETA_DOCS

# --- PÁGINA PRINCIPAL QUE VERÁN EN EL CELULAR Y PC ---
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asistencia QR - Orientación</title>
        <script src="https://unpkg.com/html5-qrcode"></script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f9; margin: 0; padding: 20px; }
            .box { max-width: 450px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            #reader { width: 100%; border: 2px solid #333; border-radius: 8px; }
            .btn { background-color: #28a745; color: white; padding: 12px; border: none; width: 100%; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 15px; }
            #status { margin-top: 15px; font-size: 18px; font-weight: bold; color: #007bff; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Escáner de Asistencia SYMEC</h2>
            <p>Control de Accesos (6E y 6F)</p>
            <div id="reader"></div>
            <div id="status">Esperando Código QR...</div>
            <button class="btn" onclick="location.href='/subir'">Subir Justificante Manual (PDF/JPG)</button>
        </div>

        <script>
            function onScanSuccess(decodedText) {
                html5QrcodeScanner.clear();
                document.getElementById('status').innerText = "Procesando registro...";
                
                fetch('/registrar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ datos: decodedText })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('status').innerHTML = "✅ " + data.msg;
                        if(confirm(data.msg + "\\n\\n¿Quieres adjuntar un Justificante (PDF/JPG) para este alumno?")) {
                            location.href = "/subir?matricula=" + data.matricula;
                        } else {
                            setTimeout(() => { location.reload(); }, 1500);
                        }
                    } else {
                        document.getElementById('status').innerText = "❌ " + data.error;
                        setTimeout(() => { location.reload(); }, 3000);
                    }
                });
            }
            let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
            html5QrcodeScanner.render(onScanSuccess);
        </script>
    </body>
    </html>
    '''

# --- PROCESAR QR EN EL EXCEL ---
@app.route('/registrar', methods=['POST'])
def registrar():
    req = request.json.get('datos', '')
    try:
        partes = req.split(" - ")
        mat = partes[0].replace("Matricula:", "").strip()
        nom = partes[1].replace("Nombre:", "").strip()
        gpo = partes[2].replace("Grupo:", "").strip()
        
        ahora = datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora = ahora.strftime("%H:%M")
        
        with open("Reporte_Asistencia_Orientacion.csv", mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([fecha, hora, mat, nom, gpo, "REGISTRO", "PRESENTE", "No Aplica"])
            
        return jsonify({"success": True, "msg": f"Registrado: {nom} ({gpo})", "matricula": mat})
    except:
        return jsonify({"success": False, "error": "Formato QR no válido"})

# --- SUBIR JUSTIFICANTES DESDE EL CELULAR ---
@app.route('/subir', methods=['GET', 'POST'])
def subir():
    mat_previa = request.args.get('matricula', '')
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        file = request.files.get('archivo')
        if file and matricula:
            ext = os.path.splitext(file.filename)[1].lower()
            nuevo_nombre = f"Justificante_{matricula}_{datetime.now().strftime('%H%M%S')}{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre))
            
            with open("Reporte_Asistencia_Orientacion.csv", mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), matricula, "Actualización Documento", "N/A", "JUSTIFICANTE", "JUSTIFICADO", nuevo_nombre])
            
            return '<script>alert("¡Justificante guardado exitosamente en la computadora central!"); window.location.href="/";</script>'
            
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Subir Documento</title></head>
    <body style="font-family:Arial; text-align:center; background:#f4f4f9; padding:20px;">
        <div style="max-width:400px; margin:auto; background:white; padding:20px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
            <h3>Cargar Justificante Médico / Reporte</h3>
            <form method="POST" enctype="multipart/form-data">
                <input type="text" name="matricula" value="{mat_previa}" placeholder="Matrícula del alumno" style="width:100%; padding:10px; margin:10px 0;" required><br>
                <input type="file" name="archivo" accept=".pdf,.jpg,.jpeg,.png" style="width:100%; margin:10px 0;" required><br><br>
                <button type="submit" style="background:#28a745; color:white; padding:12px; width:100%; border:none; border-radius:5px; font-size:16px;">Guardar en Servidor</button>
            </form>
            <br><a href="/">Volver al Escáner</a>
        </div>
    </body>
    </html>
    '''

#if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=10000)

@app.route('/descargar')
def descargar_reporte():
    try:
        return send_file('Reporte_Asistencia_Orientacion.csv', as_attachment=True)
    except Exception as e:
        return "Aún no hay registros de asistencia para descargar."
