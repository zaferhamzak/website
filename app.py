from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Veritabanı yolunu düzenleme
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database klasörünü oluştur
os.makedirs(os.path.join(basedir, 'database'), exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    image_path = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    contents = Content.query.all()
    return render_template('index.html', contents=contents)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    contents = Content.query.all()
    return render_template('admin.html', contents=contents)

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_content():
    if request.method == 'POST':
        new_content = Content(
            section=request.form.get('section'),
            title=request.form.get('title'),
            content=request.form.get('content')
        )
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.static_folder, 'img', filename))
                new_content.image_path = filename
        db.session.add(new_content)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('add_content.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_content(id):
    content = Content.query.get_or_404(id)
    if request.method == 'POST':
        content.title = request.form.get('title')
        content.content = request.form.get('content')
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.static_folder, 'img', filename))
                content.image_path = filename
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit.html', content=content)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin_user)
            
        # Add default about content if not exists
        if not Content.query.filter_by(section='about').first():
            about_content = Content(
                section='about',
                title='Hakkımızda',
                content='Bodur Oto Kurtarma olarak, 2005 yılından bu yana İstanbul ve çevre illerde 7/24 çekici ve yol yardım hizmeti sunmaktayız. Profesyonel ekibimiz ve modern araç filomuzla, aracınızın türü ve durumu ne olursa olsun en hızlı ve güvenli şekilde yardımınıza koşuyoruz.\n\nUzman kadromuz, her türlü araç çekme, kurtarma ve yol yardımı konusunda deneyimli olup, en zorlu koşullarda bile çözüm üretebilmektedir. Müşteri memnuniyetini her şeyin üstünde tutan anlayışımızla, uygun fiyat ve kaliteli hizmet garantisi veriyoruz.\n\nAcil durumlar için 7/24 çağrı merkezimiz hizmetinizdedir. Tek bir telefonla İstanbul\'un her noktasına en kısa sürede ulaşıyoruz.'
            )
            db.session.add(about_content)

        # Add services if not exists
        services = [
            {
                'title': 'Oto Çekici Hizmeti',
                'content': 'Bodur Oto Kurtarma olarak her türlü araç için profesyonel çekici hizmeti sunuyoruz. Modern çekici filomuzla aracınızı güvenle istediğiniz yere taşıyoruz. Özel ekipmanlarımız sayesinde hasarlı ve kazalı araçları da güvenle taşıyabiliyoruz.'
            },
            {
                'title': 'Yol Yardım',
                'content': 'Lastik patlaması, akü takviyesi, yakıt bitmesi gibi durumlarda hızlı yol yardım hizmeti veriyoruz. Deneyimli ekibimiz ve tam donanımlı araçlarımızla İstanbul\'un her noktasında yanınızdayız.'
            },
            {
                'title': 'Kaza Kurtarma',
                'content': 'Kaza durumlarında profesyonel kurtarma ekibimizle en kısa sürede olay yerinde olup, aracınızı güvenle kurtarıyoruz. Özel vinç sistemlerimiz ve ekipmanlarımızla her türlü kaza durumunda çözüm üretiyoruz.'
            }
        ]
        
        for service in services:
            if not Content.query.filter_by(section='services', title=service['title']).first():
                service_content = Content(
                    section='services',
                    title=service['title'],
                    content=service['content']
                )
                db.session.add(service_content)
            
        db.session.commit()
    app.run(debug=True)
