import requests

DASHBOARD_URL = "http://localhost:3000/api/update"

ports = {
    "1": {"interfaceName": "GigabitEthernet1/0/1", "status": "UP"},
    "2": {"interfaceName": "GigabitEthernet1/0/2", "status": "UP"}
}

def push_update(port_id):
    try:
        requests.post(DASHBOARD_URL, json=ports[port_id])
        print(f"[*] Sent update: {ports[port_id]['interfaceName']} -> {ports[port_id]['status']}")
    except Exception as e:
        print(f"[!] Connection Error: {e}")

if __name__ == "__main__":
    print("--- CRUISE NOC MANUAL CONTROL ---")
    while True:
        choice = input("\nToggle Port (1 or 2): ").strip()
        if choice in ports:
            ports[choice]["status"] = "DOWN" if ports[choice]["status"] == "UP" else "UP"
            push_update(choice)
