# LEGACY REFERENCE: retained during factory migration. Use run.py for new startup path.
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # wichtig, sonst blockiert dein Browser

DB_PATH = "data.db"

# Speichert die aktuelle Teleprompter-Konfiguration
current_teleprompter_config = {
    "text": "Willkommen zur AR-Brille!\n\nDies ist der Standard-Text.\nKlicke auf 'An AR-Brille senden' in der Test-Seite.",
    "speed": 30,
    "fontSize": 2,
    "fontColor": "#0f0",
    "backgroundColor": "#000",
    "fontFamily": "Courier New",
    "lineHeight": 1.5,
    "opacity": 1
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages1 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT
            )
        """)
        # Teleprompter-Konfigurationen speichern (optional)
        c.execute("""
            CREATE TABLE IF NOT EXISTS teleprompter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                speed REAL,
                fontSize REAL,
                fontColor TEXT,
                backgroundColor TEXT,
                fontFamily TEXT,
                lineHeight REAL,
                opacity REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# ==================== MESSAGES (existing) ====================

@app.route('/api/messages', methods=['GET'])
def get_messages():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, content FROM messages1 ORDER BY id DESC")
        rows = c.fetchall()
    return jsonify([{"id": r[0], "content": r[1]} for r in rows])


@app.route('/api/messages', methods=['POST'])
def add_message():
    data = request.json
    content = data.get("content")
    if not content:
        return jsonify({"error": "no content"}), 400
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO messages1 (content) VALUES (?)", (content,))
        conn.commit()
    return jsonify({"status": "ok"})


@app.route('/api/messages', methods=['DELETE'])
def delete_messages():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM messages1")
        conn.commit()
    return jsonify({"status": "all messages deleted"})


# ==================== MAIN INFO ====================

@app.route('/api/mainInfo', methods=['GET'])
def get_main_info():
    info = {
        "Battery": "85%",
        "Temperature": "36.5°C",
        "Humidity": "45%",
    }
    return jsonify(info)


# ==================== TELEPROMPTER ====================

@app.route('/api/teleprompter', methods=['GET'])
def get_teleprompter_config():
    """Für die Test-Seite – lädt die aktuelle Config"""
    return jsonify(current_teleprompter_config)


@app.route('/api/teleprompter/current', methods=['GET'])
def get_current_teleprompter():
    """Für die AR-Brille – prüft auf Updates"""
    return jsonify(current_teleprompter_config)


@app.route('/api/teleprompter/send', methods=['POST'])
def send_to_glasses():
    """Companion App sendet Config zur Brille"""
    global current_teleprompter_config
    
    try:
        data = request.json
        
        # Validierung
        required_fields = ['text', 'speed', 'fontSize', 'fontColor', 'backgroundColor', 'fontFamily', 'lineHeight', 'opacity']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "missing required fields"}), 400
        
        # Konfiguration speichern
        current_teleprompter_config = data
        
        # Optional: In DB speichern für History
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO teleprompter_history 
                (text, speed, fontSize, fontColor, backgroundColor, fontFamily, lineHeight, opacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['text'],
                data['speed'],
                data['fontSize'],
                data['fontColor'],
                data['backgroundColor'],
                data['fontFamily'],
                data['lineHeight'],
                data['opacity']
            ))
            conn.commit()
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] 📤 Teleprompter aktualisiert:")
        print(f"  Text: {data['text'][:50]}...")
        print(f"  Speed: {data['speed']} px/s")
        print(f"  Size: {data['fontSize']} rem")
        print(f"  Font: {data['fontFamily']}")
        print(f"  Color: {data['fontColor']}")
        
        return jsonify({
            "status": "success",
            "message": "Zur AR-Brille gesendet",
            "timestamp": timestamp
        }), 200
        
    except Exception as e:
        print(f"[FEHLER] {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/teleprompter/history', methods=['GET'])
def get_teleprompter_history():
    """Lädt die letzten 10 Teleprompter-Einstellungen"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, text, speed, fontSize, timestamp 
            FROM teleprompter_history 
            ORDER BY id DESC 
            LIMIT 10
        """)
        rows = c.fetchall()
    
    return jsonify([{
        "id": r[0],
        "text": r[1][:50] + "...",
        "speed": r[2],
        "fontSize": r[3],
        "timestamp": r[4]
    } for r in rows])


@app.route('/api/teleprompter/reset', methods=['POST'])
def reset_teleprompter():
    """Setzt Teleprompter auf Standard zurück"""
    global current_teleprompter_config
    
    current_teleprompter_config = {
        "text": "Willkommen zur AR-Brille!\n\nDies ist der Standard-Text.",
        "speed": 30,
        "fontSize": 2,
        "fontColor": "#0f0",
        "backgroundColor": "#000",
        "fontFamily": "Courier New",
        "lineHeight": 1.5,
        "opacity": 1
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Teleprompter zurückgesetzt")
    
    return jsonify({
        "status": "reset",
        "config": current_teleprompter_config
    }), 200


# ==================== INFO & DEBUG ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Debug-Endpunkt für allgemeine Informationen"""
    return jsonify({
        "app": "AR-Brille Backend",
        "version": "1.0",
        "endpoints": {
            "messages": "/api/messages",
            "mainInfo": "/api/mainInfo",
            "teleprompter": "/api/teleprompter",
            "teleprompter_send": "/api/teleprompter/send (POST)",
            "teleprompter_history": "/api/teleprompter/history",
            "teleprompter_reset": "/api/teleprompter/reset (POST)"
        },
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("🚀 AR-Brille Backend läuft")
    print("="*50)
    print("📍 http://localhost:5000")
    print("\nVerfügbare Endpunkte:")
    print("  • /api/messages        (GET, POST, DELETE)")
    print("  • /api/mainInfo        (GET)")
    print("  • /api/teleprompter    (GET)")
    print("  • /api/teleprompter/send       (POST)")
    print("  • /api/teleprompter/current    (GET)")
    print("  • /api/teleprompter/history    (GET)")
    print("  • /api/teleprompter/reset      (POST)")
    print("  • /api/status          (GET)")
    print("="*50 + "\n")
    
    app.run(debug=True)
