from flask import Flask, redirect, request, session, render_template, url_for
import requests
import re
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

STEAM_API_KEY = '8C9877E691C84ED816FEF5D1B80A842B'
RETURN_URL = 'http://localhost:5000/authorize'

STEAM_OPENID_URL = 'https://steamcommunity.com/openid/login'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': RETURN_URL,
        'openid.realm': 'http://localhost:5000/',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select'
    }
    query_string = urlencode(params)
    return redirect(f"{STEAM_OPENID_URL}?{query_string}")

@app.route('/authorize')
def authorize():
    # Verifica a resposta com Steam
    params = {
        'openid.assoc_handle': request.args.get('openid.assoc_handle'),
        'openid.signed': request.args.get('openid.signed'),
        'openid.sig': request.args.get('openid.sig'),
        'openid.ns': request.args.get('openid.ns')
    }

    for item in request.args.get('openid.signed').split(','):
        param_key = f"openid.{item}"
        params[param_key] = request.args.get(param_key)

    params['openid.mode'] = 'check_authentication'
    response = requests.post(STEAM_OPENID_URL, data=params)

    if "is_valid:true" not in response.text:
        return "Erro ao validar login com a Steam."

    steam_id_match = re.search(r'https://steamcommunity.com/openid/id/(\d+)', request.args['openid.claimed_id'])
    if not steam_id_match:
        return "SteamID inválido."

    steam_id = steam_id_match.group(1)
    session['steam_id'] = steam_id

    # Buscar perfil na API Steam
    profile_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
    profile_data = requests.get(profile_url).json()
    player = profile_data['response']['players'][0]

    session['username'] = player['personaname']
    session['avatar'] = player['avatarfull']

    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'steam_id' not in session:
        return redirect(url_for('index'))
    return render_template('profile.html',
                           username=session['username'],
                           avatar=session['avatar'],
                           steam_id=session['steam_id'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
