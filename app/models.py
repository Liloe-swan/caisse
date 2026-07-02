from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///caisse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)         
    
   
    ventes = db.relationship('Vente', backref='caissier', lazy=True)


class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    
    
    produits = db.relationship('Produit', backref='fournisseur', lazy=True)


class Produit(db.Model):
    __tablename__ = 'produits'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    code_barre = db.Column(db.String(50), unique=True, nullable=False) 
    prix_achat = db.Column(db.Float, nullable=False)
    prix_vente = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, nullable=False, default=0)  
    date_peremption = db.Column(db.Date, nullable=True)                
    
   
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=True)
    

    details_ventes = db.relationship('DetailVente', backref='produit', lazy=True)


class Vente(db.Model):
    __tablename__ = 'ventes'
    id = db.Column(db.Integer, primary_key=True) 
    date_vente = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    mode_paiement = db.Column(db.String(30), nullable=False) 
    
    
    caissier_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    
 
    details = db.relationship('DetailVente', backref='vente', lazy=True)


class DetailVente(db.Model):
    __tablename__ = 'details_ventes'
    id = db.Column(db.Integer, primary_key=True)
    vente_id = db.Column(db.Integer, db.ForeignKey('ventes.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    quantite_vendue = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False) 


def initialiser_la_base():
    with app.app_context():
        db.create_all()
        print("La base de données et les tables ont été créées avec succès !")

if __name__ == '__main__':
     initialiser_la_base()