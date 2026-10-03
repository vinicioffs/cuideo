from flask import Flask, render_template_string, request, jsonify
import webbrowser
from threading import Timer
import json
import os

app = Flask(__name__)

DATA_FILE = 'calendar_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendario Local</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            /* El fondo de fuera del calendario ahora es un color oscuro y elegante */
            background-color: #1e293b; 
            min-height: 100vh;
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        #calendar-container { 
            width: 100%; 
            max-width: 1200px; 
            
            /* LA IMAGEN AHORA ESTÁ DENTRO DEL CALENDARIO */
            background-image: url('/static/image.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        }
        
        .header-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            /* Fondo sutil para que los botones y el título se lean bien sobre la foto */
            background: rgba(255, 255, 255, 0.7);
            padding: 10px 20px;
            border-radius: 8px;
            backdrop-filter: blur(5px);
        }
        .header-controls button {
            background-color: #2196f3;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s, transform 0.1s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .header-controls button:hover { background-color: #1976d2; }
        .header-controls button:active { transform: scale(0.95); }
        h1 { margin: 0; color: #111; text-transform: uppercase; }

        .weekdays { 
            display: grid; 
            grid-template-columns: repeat(7, 1fr); 
            font-weight: bold; 
            text-align: center; 
            margin-bottom: 10px; 
            color: #222;
            background: rgba(255, 255, 255, 0.7); /* Franja semitransparente */
            padding: 10px 0;
            border-radius: 6px;
            backdrop-filter: blur(5px);
        }
        #calendar-grid { 
            display: grid; 
            grid-template-columns: repeat(7, 1fr); 
            gap: 10px; 
            auto-rows: 140px; 
        }
        .day { 
            position: relative; 
            height: 120px; 
            border: 1px solid rgba(255,255,255,0.3); 
            border-radius: 6px; 
            display: flex; 
            flex-direction: column; 
            overflow: hidden; 
            /* CASILLAS SEMITRANSPARENTES PARA VER LA FOTO */
            background: rgba(255, 255, 255, 0.4); 
            backdrop-filter: blur(2px); /* Ligero desenfoque cristalino */
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .current-day {
            border: 3px solid #ff9800; 
            box-shadow: 0 0 15px rgba(255, 152, 0, 0.8); 
            transform: scale(1.03); 
            z-index: 2; 
        }
        
        .half { 
            flex: 1; 
            display: flex;
            align-items: center;
            justify-content: flex-end; 
            padding-right: 10px;
            transition: background 0.3s ease; 
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        .half:last-child { border-bottom: none; }
        
        /* Colores automatizados más transparentes para no tapar la foto (0.75 de opacidad) */
        .bg-none { background: transparent; }
        .bg-green { background: rgba(76, 175, 80, 0.75); }
        .bg-red { background: rgba(244, 67, 54, 0.75); }
        .bg-fuchsia { background: rgba(255, 0, 255, 0.75); }

        .date-number { 
            position: absolute; 
            top: 5px; 
            left: 5px; 
            font-weight: bold; 
            font-size: 1.1rem;
            color: #333; 
            background: rgba(255,255,255,0.9);
            padding: 2px 6px;
            border-radius: 4px;
            pointer-events: none; 
            z-index: 10;
        }
        
        .current-day .date-number {
            background: #ff9800;
            color: white;
        }

        input { 
            width: 70%; 
            padding: 4px 6px; 
            text-align: left; 
            border: 1px solid rgba(0,0,0,0.3); 
            border-radius: 4px; 
            font-size: 14px; 
            font-weight: 600;
            color: #111;
            background: rgba(255, 255, 255, 0.6); 
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            pointer-events: auto; 
            transition: background 0.2s;
        }
        input:focus { 
            background: rgba(255, 255, 255, 0.95); 
            outline: 2px solid #2196f3; 
            border-color: #2196f3;
        }
    </style>
</head>
<body>

    <div id="calendar-container">
        <div class="header-controls">
            <button onclick="changeMonth(-1)">&#10094; Anterior</button>
            <h1 id="month-name">Calendario</h1>
            <button onclick="changeMonth(1)">Siguiente &#10095;</button>
        </div>
        <div class="weekdays">
            <div>Lunes</div><div>Martes</div><div>Miércoles</div><div>Jueves</div><div>Viernes</div><div>Sábado</div><div>Domingo</div>
        </div>
        <div id="calendar-grid"></div>
    </div>

    <script>
        let currentDate = new Date();
        let currentMonth = currentDate.getMonth();
        let currentYear = currentDate.getFullYear();
        const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];

        const realToday = new Date();
        const todayStr = `${realToday.getFullYear()}-${String(realToday.getMonth()+1).padStart(2, '0')}-${String(realToday.getDate()).padStart(2, '0')}`;

        function applyAutoColor(inputEl) {
            const text = inputEl.value.toLowerCase().trim();
            const halfEl = inputEl.parentElement;
            
            halfEl.classList.remove('bg-none', 'bg-red', 'bg-green', 'bg-fuchsia');

            if (text.includes('alberto')) {
                halfEl.classList.add('bg-red');
            } else if (text.includes('manuel')) {
                halfEl.classList.add('bg-green');
            } else if (text.includes('elena')) {
                halfEl.classList.add('bg-fuchsia');
            } else {
                halfEl.classList.add('bg-none');
            }
        }

        async function saveAllData() {
            const data = {};
            document.querySelectorAll('.day').forEach(dayEl => {
                const date = dayEl.dataset.date;
                if(!date) return;
                
                const halves = dayEl.querySelectorAll('.half');
                if(halves.length === 2) {
                    const topColor = Array.from(halves[0].classList).find(c => c.startsWith('bg-'));
                    const topText = halves[0].querySelector('input').value;
                    
                    const bottomColor = Array.from(halves[1].classList).find(c => c.startsWith('bg-'));
                    const bottomText = halves[1].querySelector('input').value;
                    
                    data[date] = {
                        top: { color: topColor, text: topText },
                        bottom: { color: bottomColor, text: bottomText }
                    };
                }
            });

            await fetch('/api/data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        function changeMonth(offset) {
            let newDate = new Date(currentYear, currentMonth + offset, 1);
            currentYear = newDate.getFullYear();
            currentMonth = newDate.getMonth();
            renderCalendar(currentYear, currentMonth);
        }

        function renderCalendar(year, month) {
            const grid = document.getElementById('calendar-grid');
            grid.innerHTML = ''; 

            document.getElementById('month-name').textContent = monthNames[month] + " " + year;

            const firstDay = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            
            let startDay = firstDay === 0 ? 6 : firstDay - 1;

            for (let i = 0; i < startDay; i++) {
                grid.innerHTML += '<div></div>';
            }

            for (let i = 1; i <= daysInMonth; i++) {
                let dayDiv = document.createElement('div');
                dayDiv.className = 'day';
                
                const dateStr = `${year}-${String(month+1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
                dayDiv.dataset.date = dateStr;

                if (dateStr === todayStr) {
                    dayDiv.classList.add('current-day');
                }

                dayDiv.innerHTML = `
                    <div class="date-number">${i}</div>
                    <div class="half bg-none">
                        <input type="text" placeholder="Nombre..." oninput="applyAutoColor(this)" onchange="saveAllData()">
                    </div>
                    <div class="half bg-none">
                        <input type="text" placeholder="Nombre..." oninput="applyAutoColor(this)" onchange="saveAllData()">
                    </div>
                `;
                grid.appendChild(dayDiv);
            }
            
            loadSavedData();
        }

        async function loadSavedData() {
            const res = await fetch('/api/data');
            const data = await res.json();
            
            document.querySelectorAll('.day').forEach(dayEl => {
                const date = dayEl.dataset.date;
                if(data[date]) {
                    const halves = dayEl.querySelectorAll('.half');
                    
                    const topInput = halves[0].querySelector('input');
                    topInput.value = data[date].top.text || '';
                    applyAutoColor(topInput); 
                    
                    const bottomInput = halves[1].querySelector('input');
                    bottomInput.value = data[date].bottom.text || '';
                    applyAutoColor(bottomInput); 
                }
            });
        }

        renderCalendar(currentYear, currentMonth);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/data', methods=['POST'])
def update_data():
    incoming_data = request.json
    existing_data = load_data()
    existing_data.update(incoming_data)
    save_data(existing_data)
    return jsonify({"status": "success"})

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)