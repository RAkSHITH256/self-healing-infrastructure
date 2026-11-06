
from flask import Flask, request, jsonify
import subprocess
import logging
import time
import threading

app = Flask(__name__)

logging.basicConfig(
    filename="/app/logs/recovery.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

COOLDOWN_SECONDS = 120
last_recovery_time = 0
recovery_lock = threading.Lock()

@app.route("/alerts", methods=["POST"])
def receive_alert():
    global last_recovery_time

    data = request.json or {}

    for alert in data.get("alerts", []):
        alert_name = alert.get("labels", {}).get("alertname")
        status = alert.get("status")

        if alert_name == "NginxDown" and status == "firing":

            with recovery_lock:
                current_time = time.time()

                if current_time - last_recovery_time < COOLDOWN_SECONDS:
                    logging.info("Recovery skipped: cooldown active.")
                    return jsonify({
                        "message": "Recovery skipped: cooldown active"
                    }), 200

                last_recovery_time = current_time

            logging.info("NGINX failure detected. Starting Ansible recovery.")

            try:
                result = subprocess.run(
                    [
                        "ansible-playbook",
                        "/app/ansible/recovery.yml",
                        "-i",
                        "/app/ansible/inventory.ini"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                logging.info(result.stdout)

                if result.returncode == 0:
                    logging.info("NGINX recovery successful.")
                    return jsonify({
                        "message": "Recovery successful"
                    }), 200

                logging.error(result.stderr)
                logging.error("NGINX recovery failed.")

                return jsonify({
                    "message": "Recovery failed"
                }), 500

            except subprocess.TimeoutExpired:
                logging.error("Ansible recovery timed out.")
                return jsonify({
                    "message": "Recovery timed out"
                }), 500

    return jsonify({"message": "No recovery action required"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
