import os
import json
import paramiko
from plexapi.server import PlexServer
from flask import Flask, jsonify, render_template
from retrying import retry

app = Flask(__name__)

CONFIG_FILE = '/app/config.json'
PLEX_USERS_FILE = '/app/plex_users.json'
PRIVATE_KEY_FILE = '/root/.ssh/id_rsa'  # Path where the key will be mounted in the container

def load_config():
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def ensure_directory_exists(filepath):
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_plex_users(data):
    ensure_directory_exists(PLEX_USERS_FILE)
    with open(PLEX_USERS_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def log(message):
    print(message)

config = load_config()

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def ssh_connect(ip, port, user, timeout=30):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey(filename=PRIVATE_KEY_FILE)
    ssh.connect(ip, port=port, username=user, pkey=private_key, timeout=timeout)
    return ssh

def fetch_preferences_via_ssh(ssh, paths):
    preferences = []
    for path in paths:
        stdin, stdout, stderr = ssh.exec_command(f'find "{path}" -maxdepth 6 -type f -name "Preferences.xml"')
        preferences += stdout.read().decode().splitlines()
    return preferences

def extract_url_token(preferences_file, node_ip):
    try:
        with open(preferences_file, 'r') as file:
            content = file.read()
        token = content.split('PlexOnlineToken="')[1].split('"')[0]
        port = content.split('ManualPortMappingPort="')[1].split('"')[0]
        return f"http://{node_ip}:{port}/", token
    except Exception as e:
        log(f"Error extracting URL and token: {e}")
        return None, None

def fetch_plex_servers():
    servers = []
    for node in config['nodes']:
        log(f"Processing node: {node['name']} ({node['ip']})")
        if node['local_access']:
            for path in node['paths']:
                if os.path.isdir(path):
                    for user_dir in os.listdir(path):
                        pref_path = os.path.join(path, user_dir, "Library/Application Support/Plex Media Server/Preferences.xml")
                        if os.path.isfile(pref_path):
                            url, token = extract_url_token(pref_path, node['ip'])
                            if url and token:
                                servers.append({'name': node['name'], 'url': url, 'token': token})
        else:
            ssh = ssh_connect(node['ip'], node['port'], config['SSH_USER'])
            preferences_files = fetch_preferences_via_ssh(ssh, node['paths'])
            for pref_file in preferences_files:
                local_file = os.path.join("/tmp", os.path.basename(pref_file))
                sftp = ssh.open_sftp()
                sftp.get(pref_file, local_file)
                sftp.close()
                url, token = extract_url_token(local_file, node['ip'])
                if url and token:
                    servers.append({'name': node['name'], 'url': url, 'token': token})
            ssh.close()
    save_plex_users(servers)
    return servers

def monitor_servers():
    servers = fetch_plex_servers()
    data = []
    for server in servers:
        plex = PlexServer(server['url'], server['token'])
        sessions = plex.sessions()
        for session in sessions:
            user = session.usernames[0]
            try:
                state = session.state
            except AttributeError:
                state = 'unknown'
            transcode = session.transcodeSession
            video_decision = transcode.videoDecision if transcode else 'Direct Play'
            ip_address = session.session.location.ip
            media = session.nowPlaying[0]
            poster_url = plex.transcodeImageUrl(media.thumb, width=200)
            data.append({
                'server': server['name'],
                'user': user,
                'state': state,
                'bandwidth': session.bandwidth,
                'transcode': video_decision,
                'ip_address': ip_address,
                'title': media.title,
                'poster': poster_url,
                'type': media.type
            })
    return data

@app.route('/monitor')
def monitor():
    data = monitor_servers()
    return jsonify(data)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
