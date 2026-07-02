from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models import db, Utilisateur, Produit, Fournisseur, Vente, DetailVente

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///caisse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'cle_secrete_pour_la_session_11'

db.init_app(app)

with app.app_context():
    db.create_all()
    
@app.route('/inscription', methods=['GET', 'POST'])
def inscription(): 
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        role = request.form['role']
        
        user_existe = Utilisateur.query.filter_by(email=email).first()
        if user_existe:
            flash("cet email existe déjà !")
            return redirect(url_for('inscription'))
        
        nouveau_user = Utilisateur(nom=nom, email=email, mot_de_passe=mot_de_passe, role=role)
        db.session.addd(nouveau_user)
        db.session.commit
        
        flash("inscription reussie ! Vous pouvez vous connecter")
        return redirect(url_for('login'))
    
    return render_template('inscription.html')

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' :
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        
        user = Utilisateur.query.filter_by(email=email, mot_de_passe=mot_de_passe).first()
        
        if user:
            session['user_id'] = user.id
            session['user_nom'] = user.nom
            session['user_role'] = user.role
            
            flash(f"Bienvenue {user.nom} !")
            return redirect(url_for('acceuil'))
        
        else:
            flash("Email ou mot de passe incorrect.")
            return redirect(url_for('login'))
    
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("vous avez été déconnecté")
    return redirect(url_for('login'))
            