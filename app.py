import os
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=64))

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)

# پایگاه داده ادمین‌ها و قابلیت تغییر رمز
admin_accounts = {
    "admin": "admin"
}

FIXED_PORT = 2053

# سیستم لاگ خطاها و وضعیت رخدادها
system_error_logs = [
    {"id": 1, "time": "14:22:10", "level": "INFO", "message": "هسته کوانتومی روی پورت 2053 با موفقیت Bind شد."},
    {"id": 2, "time": "15:05:45", "level": "WARNING", "message": "تلاش ناموفق برای ورود از آی‌پی ناشناس (سیستم ضد بروت‌فورس فعال شد)."},
    {"id": 3, "time": "16:40:12", "level": "SUCCESS", "message": "ساب‌لینک چندکانفیگه با موفقیت به‌روزرسانی شد."}
]

system_state = {
    "telegram_token": "791234567:AAH_IranMottasel_Enterprise_Bot",
    "core_version": "v12.0-Ultimate-Core",
    "failed_attempts": 0,
    "lockout_time": None
}

active_configs_database = [
    {"id": 1, "name": "Iran-Mottasel-VLESS-Reality", "protocol": "VLESS", "port": FIXED_PORT, "status": "Stable", "traffic": "210.4 GB", "uuid": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"},
    {"id": 2, "name": "Iran-Mottasel-Trojan-Stealth", "protocol": "Trojan", "port": FIXED_PORT, "status": "Secure", "traffic": "385.2 GB", "uuid": "c92a5gbv-8fed-22e1-b876-11b1d82f7cg7"},
    {"id": 3, "name": "Iran-Mottasel-Shadowsocks-Pro", "protocol": "Shadowsocks", "port": FIXED_PORT, "status": "Active", "traffic": "114.9 GB", "uuid": "a34b6hju-9iop-33f2-c987-22c2e93h8dh8"}
]

@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def dashboard_home():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('index.html', port=FIXED_PORT, configs=active_configs_database, state=system_state, logs=system_error_logs, admins=list(admin_accounts.keys()))

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if system_state['lockout_time'] and datetime.now() < system_state['lockout_time']:
        rem = int((system_state['lockout_time'] - datetime.now()).total_seconds())
        return render_template('login.html', error=f'امنیت سیستم: ورود قفل است. لطفاً {rem} ثانیه صبر کنید.')

    error_msg = None
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        
        if user in admin_accounts and admin_accounts[user] == pwd:
            system_state['failed_attempts'] = 0
            session.permanent = True
            session['logged_in'] = True
            session['current_user'] = user
            system_error_logs.insert(0, {"id": len(system_error_logs)+1, "time": datetime.now().strftime("%H:%M:%S"), "level": "INFO", "message": f"ادمین {user} با موفقیت وارد پنل شد."})
            return redirect(url_for('dashboard_home'))
        else:
            system_state['failed_attempts'] += 1
            if system_state['failed_attempts'] >= 5:
                system_state['lockout_time'] = datetime.now() + timedelta(minutes=1)
                error_msg = 'هشدار امنیتی: ۵ تلاش ناموفق. دسترسی برای ۱ دقیقه محدود شد.'
            else:
                error_msg = f'خطا: نام کاربری یا رمز عبور اشتباه است. (تلاش {system_state["failed_attempts"]} از ۵)'
                
    return render_template('login.html', error=error_msg)

@app.route('/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/api/admin/change-password', methods=['POST'])
def api_change_password():
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json or {}
    current_user = session.get('current_user')
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')
    
    if admin_accounts.get(current_user) != old_pass:
        return jsonify({'status': 'error', 'message': 'رمز عبور فعلی اشتباه است.'}), 400
        
    if not new_pass or len(new_pass) < 4:
        return jsonify({'status': 'error', 'message': 'رمز عبور جدید باید حداقل ۴ کاراکتر باشد.'}), 400
        
    admin_accounts[current_user] = new_pass
    system_error_logs.insert(0, {"id": len(system_error_logs)+1, "time": datetime.now().strftime("%H:%M:%S"), "level": "SUCCESS", "message": f"رمز عبور ادمین {current_user} با موفقیت تغییر کرد."})
    return jsonify({'status': 'success', 'message': 'رمز عبور با موفقیت آپدیت شد.'})

@app.route('/api/admin/add', methods=['POST'])
def api_add_admin():
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    data = request.json or {}
    new_user = data.get('username')
    new_pwd = data.get('password')
    
    if not new_user or not new_pwd:
        return jsonify({'status': 'error', 'message': 'نام کاربری و رمز عبور الزامی است.'}), 400
        
    if new_user in admin_accounts:
        return jsonify({'status': 'error', 'message': 'این نام کاربری از قبل وجود دارد.'}), 400
        
    admin_accounts[new_user] = new_pwd
    system_error_logs.insert(0, {"id": len(system_error_logs)+1, "time": datetime.now().strftime("%H:%M:%S"), "level": "INFO", "message": f"ادمین جدید با نام {new_user} اضافه شد."})
    return jsonify({'status': 'success', 'message': 'مدیر جدید با موفقیت به پنل اضافه شد.'})

@app.route('/api/configs/create', methods=['POST'])
def api_create_config():
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    req_data = request.json or {}
    name = req_data.get('name', f'Iran-Mottasel-Node-{len(active_configs_database) + 1}')
    protocol = req_data.get('protocol', 'VLESS')
    
    new_id = len(active_configs_database) + 1
    new_uuid = '-'.join([''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) for _ in range(5)])
    
    new_item = {
        "id": new_id,
        "name": name,
        "protocol": protocol,
        "port": FIXED_PORT,
        "status": "Operational",
        "traffic": "0.0 GB",
        "uuid": new_uuid
    }
    active_configs_database.append(new_item)
    system_error_logs.insert(0, {"id": len(system_error_logs)+1, "time": datetime.now().strftime("%H:%M:%S"), "level": "SUCCESS", "message": f"کانفیگ جدید ({name}) ایجاد شد."})
    return jsonify({'status': 'success', 'message': 'کانفیگ با موفقیت روی پورت ثابت ایجاد شد.', 'data': new_item})

@app.route('/api/configs/delete/<int:config_id>', methods=['DELETE'])
def api_delete_config(config_id):
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    global active_configs_database
    active_configs_database = [c for c in active_configs_database if c['id'] != config_id]
    system_error_logs.insert(0, {"id": len(system_error_logs)+1, "time": datetime.now().strftime("%H:%M:%S"), "level": "WARNING", "message": f"کانفیگ با شناسه {config_id} حذف شد."})
    return jsonify({'status': 'success', 'message': 'کانفیگ با موفقیت از سیستم حذف شد.'})

@app.route('/api/telegram/update', methods=['POST'])
def api_update_telegram():
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    data = request.json or {}
    token = data.get('token')
    if token:
        system_state['telegram_token'] = token
        return jsonify({'status': 'success', 'message': 'توکن ربات تلگرام با موفقیت بروز شد.'})
    return jsonify({'status': 'error', 'message': 'توکن نامعتبر است.'}), 400

if __name__ == '__main__':
    port_env = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port_env, debug=False)
