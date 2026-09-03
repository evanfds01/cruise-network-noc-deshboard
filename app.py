from flask import Flask, redirect, render_template_string, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://root:1111@localhost:3306/noc_dashboard'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Database Models
class DeviceStatus(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  interface = db.Column(db.String(50), unique=True, nullable=False)
  status = db.Column(db.String(10), nullable=False, default='UP')


class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  interface = db.Column(db.String(50), nullable=False)
  assigned = db.Column(db.String(50), nullable=False)
  status = db.Column(db.String(20), nullable=False)


class Incident(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  interface = db.Column(db.String(50), nullable=False)
  assigned = db.Column(db.String(50), nullable=False, default='Unassigned')


active_crew = [
    'Evan (IT Manager)',
    'Tejas (IT Officer)',
    'Dnyanesh (IT Technician)',
]
on_call_crew = [
    'Arjun (Systems Specialist)',
    'Nikhil (Network Administrator)',
    'Vikram (Cyber Defense Specialist)',
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');
            body { font-family: 'Inter', sans-serif; background: #0b0e14; color: #e0e0e0; padding: 30px; line-height: 1.6; }
            h1 { font-family: 'Playfair Display', serif; color: #fff; text-align: center; margin-bottom: 40px; font-size: 2.5rem; letter-spacing: -0.5px; border-bottom: 1px solid #30363d; padding-bottom: 20px; }
            .grid { display: grid; grid-template-columns: 1fr 380px; gap: 25px; max-width: 1200px; margin: auto; }
            .card { background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            h3 { color: #58a6ff; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 0; padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
            
            .UP, .DOWN { padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; text-decoration: none; transition: 0.3s; }
            .UP { background: #1f6434; color: #aff5b4; }
            .DOWN { background: #8e1515; color: #ffb8b8; }
            
            .device-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #21262d; }
            .crew-badge { background: #1f242c; padding: 8px 12px; margin: 4px 0; border-radius: 4px; border-left: 3px solid #3fb950; font-size: 0.85rem; }
            .standby-badge { background: #1f242c; padding: 8px 12px; margin: 4px 0; border-radius: 4px; border-left: 3px solid #d29922; font-size: 0.85rem; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th { color: #8b949e; font-size: 0.7rem; text-transform: uppercase; text-align: left; padding: 8px; }
            td { padding: 8px; border-bottom: 1px solid #30363d; font-size: 0.85rem; }
            
            .modal { display: {{ 'flex' if current_incident else 'none' }}; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(5px); justify-content: center; align-items: center; z-index: 100; }
            .modal-card { width: 400px; background: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; }
            button { cursor: pointer; padding: 8px 14px; border-radius: 4px; border: none; font-weight: 600; font-size: 0.85rem; }
            .modal-card button:nth-child(1) { background: #238636; color: white; }
            .modal-card button:nth-child(2) { background: #30363d; color: white; margin-left: 10px; }
            .action-btn-group { display: flex; gap: 5px; }
            .action-btn { background: #21262d; color: #58a6ff; border: 1px solid #30363d; padding: 4px 10px; font-size: 0.75rem; border-radius: 4px; text-decoration: none; font-weight: 600; }
            .action-btn:hover { background: #30363d; }
        </style>
    </head>
    <body>
        <h1>Cruise Network NOC Dashboard</h1>
        <div class="grid">
            <div>
                <div class="card">
                    <h3>Core Infrastructure</h3>
                    <div class="device-row">Bridge Link: <a href="/api/toggle?iface=Core-Bridge" class="{{ status_map.get('Core-Bridge', 'UP') }}">{{ status_map.get("Core-Bridge", "UP") }}</a></div>
                    <div class="device-row">Passenger Hub: <a href="/api/toggle?iface=Core-Passenger" class="{{ status_map.get('Core-Passenger', 'UP') }}">{{ status_map.get("Core-Passenger", "UP") }}</a></div>
                </div>
                {% for d in range(1, 7) %}
                    <div class="card">
                        <h3>Deck {{ d }}</h3>
                        {% for key, val in status_map.items() %}
                            {% if key.startswith('D' ~ d) %}
                                <div class="device-row">{{ key.split('-')[1:] | join(' ') }}: <a href="/api/toggle?iface={{ key }}" class="{{ val }}">{{ val }}</a></div>
                            {% endif %}
                        {% endfor %}
                    </div>
                {% endfor %}
            </div>
            <div>
                <div class="card">
                    <h3>Personnel Status</h3>
                    {% for e in active_crew %}
                        <div class="crew-badge">{{ e }}</div>
                    {% endfor %}
                    <div style="margin-top:15px"></div>
                    {% for e in on_call_crew %}
                        <div class="standby-badge">{{ e }}</div>
                    {% endfor %}
                </div>
                <div class="card">
                    <h3>
                        Live Tickets 
                        <div class="action-btn-group">
                            <a href="/reset-tickets" class="action-btn">Reset</a>
                            <button class="action-btn" onclick="location.reload()">Refresh</button>
                        </div>
                    </h3>
                    <table>
                        <tr><th>Device</th><th>Lead</th><th>Status</th></tr>
                        {% for t in tasks %}
                            <tr><td>{{ t.interface.split('-')[0] }}</td><td>{{ t.assigned.split(' ')[0] }}</td><td>{{ t.status }}</td></tr>
                        {% endfor %}
                    </table>
                </div>
            </div>
        </div>
        <div class="modal">
            <div class="modal-card">
                <h3>System Incident Detected</h3>
                <p>Affected: <strong>{{ current_incident.interface if current_incident else '' }}</strong></p>
                <select style="width:100%; padding:8px; margin: 15px 0; background:#0d1117; color:#fff; border:1px solid #30363d;" onchange="location.href='/api/assign?emp='+this.value">
                    <option>Assign Crew...</option>
                    {% for e in active_crew + on_call_crew %}
                        <option value="{{ e }}">{{ e }}</option>
                    {% endfor %}
                </select>
                <button onclick="location.href='/clear'">Acknowledge</button>
                <button onclick="location.href='/close-alert'">Cancel</button>
            </div>
        </div>
    </body>
</html>
"""


def init_db():
  with app.app_context():
    db.create_all()
    initial_devices = [
        'Core-Bridge',
        'Core-Passenger',
        'D1-Reception-PC',
        'D1-Lobby-WiFi',
        'D2-Casino-Slot-A',
        'D2-Bar-Printer',
        'D3-Dining-Display',
        'D3-Kitchen-Terminal',
        'D4-Theater-Projector',
        'D4-Stage-Audio',
        'D5-Cabin-WiFi-Hub',
        'D5-Info-Kiosk',
        'D6-Pool-WiFi',
        'D6-Spa-Terminal',
    ]
    for dev in initial_devices:
      if not DeviceStatus.query.filter_by(interface=dev).first():
        db.session.add(DeviceStatus(interface=dev, status='UP'))
    db.session.commit()


@app.route('/')
def index():
  devices = DeviceStatus.query.all()
  status_map = {d.interface: d.status for d in devices}
  current_incident = Incident.query.first()
  tasks = Task.query.all()

  return render_template_string(
      HTML_TEMPLATE,
      status_map=status_map,
      current_incident=current_incident,
      tasks=tasks,
      active_crew=active_crew,
      on_call_crew=on_call_crew,
  )


@app.route('/api/toggle')
def toggle():
  iface = request.args.get('iface')
  device = DeviceStatus.query.filter_by(interface=iface).first()
  current_incident = Incident.query.first()

  if device:
    if device.status == 'DOWN':
      device.status = 'UP'
      tasks = Task.query.filter_by(interface=iface).all()
      if tasks:
        for task in tasks:
          task.status = 'Cleared'
      else:
        new_task = Task(interface=iface, assigned='System', status='Cleared')
        db.session.add(new_task)

      if current_incident and current_incident.interface == iface:
        db.session.delete(current_incident)
    else:
      device.status = 'DOWN'
      if not current_incident:
        new_incident = Incident(interface=iface, assigned='Unassigned')
        db.session.add(new_incident)
    db.session.commit()
  return redirect('/')


@app.route('/api/assign')
def assign():
  emp = request.args.get('emp')
  current_incident = Incident.query.first()
  if current_incident:
    current_incident.assigned = emp
    db.session.commit()
  return redirect('/')


@app.route('/clear')
def clear():
  current_incident = Incident.query.first()
  if current_incident and current_incident.assigned != 'Unassigned':
    new_task = Task(
        interface=current_incident.interface,
        assigned=current_incident.assigned,
        status='Under Maintenance',
    )
    db.session.add(new_task)
    db.session.delete(current_incident)
    db.session.commit()
  return redirect('/')


@app.route('/close-alert')
def close_alert():
  current_incident = Incident.query.first()
  if current_incident:
    device = DeviceStatus.query.filter_by(
        interface=current_incident.interface
    ).first()
    if device:
      device.status = 'UP'
    db.session.delete(current_incident)
    db.session.commit()
  return redirect('/')


@app.route('/reset-tickets')
def reset_tickets():
  Task.query.delete()
  db.session.commit()
  return redirect('/')


if __name__ == '__main__':
  init_db()
  app.run(debug=True, port=3000)