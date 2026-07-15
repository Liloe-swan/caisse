from datetime import datetime, timezone, date
from flask_login import UserMixin 
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default="vendeur")
    mot_de_passe = db.Column(db.String(255), nullable=False)
    is_online = db.Column(db.Boolean, default=False)
    
    # Relations
    ventes = db.relationship('Vente', backref='caissier', lazy=True)
    
    def set_password(self, mot_de_passe):
        self.mot_de_passe = generate_password_hash(mot_de_passe)
        
    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe, mot_de_passe)
    
    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur}>"


@login_manager.user_loader
def load_user(user_id):
    """Indique à Flask-Login comment retrouver un utilisateur à partir de son id."""
    return Utilisateur.query.get(int(user_id))


class Categorie(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    
    # Relations
    produits = db.relationship('Produit', backref='categorie', lazy=True)

    def __repr__(self):
        return self.nom  # Retourne directement le nom pour l'affichage dynamique dans le template


class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)  
    adresse = db.Column(db.String(200), nullable=True)  
    tva_defaut = db.Column(db.Float, nullable=False, default=20.0)
    
    # Relations
    produits = db.relationship('Produit', backref='fournisseur', lazy=True)

    def __repr__(self):
        return f"<Fournisseur {self.nom}>"


class Produit(db.Model):
    __tablename__ = 'produits'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    code_barres = db.Column(db.String(50), unique=True, nullable=True)  
    prix_achat = db.Column(db.Float, nullable=False)
    prix_vente = db.Column(db.Float, nullable=False) # Prix de vente de base (HT)
    stock = db.Column(db.Integer, nullable=False, default=0)  
    seuil_alerte = db.Column(db.Integer, default=5)
    
    # ⏳ Gestion de la Péremption
    date_peremption = db.Column(db.Date, nullable=True) 
    alerte_peremption_jours = db.Column(db.Integer, default=30)
    
    # 💰 Gestion de la TVA
    taux_tva = db.Column(db.Float, nullable=False, default=18.0)
    
    # 🔗 Clés étrangères
    categorie_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=False)
    
    # Relations
    details_ventes = db.relationship('DetailVente', backref='produit', lazy=True)

    # --- PONT DE COMPATIBILITÉ : NOM / DESIGNATION ---
    @property
    def designation(self):
        """Permet d'utiliser produit.designation dans les templates HTML."""
        return self.nom

    @designation.setter
    def designation(self, value):
        self.nom = value

    # --- CALCULS DE PÉREMPTION ---
    @property
    def est_perime(self):
        """Vérifie si le produit est actuellement périmé."""
        if self.date_peremption:
            return date.today() >= self.date_peremption
        return False

    @property
    def proche_peremption(self):
        """Vérifie si le produit approche de sa date de péremption."""
        if self.date_peremption:
            jours_restants = (self.date_peremption - date.today()).days
            return 0 <= jours_restants <= self.alerte_peremption_jours
        return False

    # --- PONT DE COMPATIBILITÉ : PRIX HT / TTC ---
    @property
    def prix_vente_ttc(self):
        """Calcule automatiquement le prix de vente TTC basé sur le taux_tva."""
        return round(self.prix_vente * (1 + (self.taux_tva / 100)), 2)

    @property
    def prix_ttc(self):
        """Alias pour correspondre à l'écriture produit.prix_ttc dans le template HTML et les routes."""
        return self.prix_vente_ttc

    @prix_ttc.setter
    def prix_ttc(self, value):
        """Si on lui passe un prix_ttc directement, on calcule et stocke sa base HT."""
        self.prix_vente = round(float(value) / (1 + (self.taux_tva / 100)), 2)

    @property
    def montant_tva_vente(self):
        """Calcule le montant exact de la TVA par unité vendue."""
        return round(self.prix_vente * (self.taux_tva / 100), 2)

    def __repr__(self):
        return f"<Produit {self.nom} - TVA: {self.taux_tva}%>"


class Vente(db.Model):
    __tablename__ = 'ventes'
    
    id = db.Column(db.Integer, primary_key=True) 
    date_vente = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    total = db.Column(db.Float, nullable=False) # Total TTC cumulé de la vente
    total_tva = db.Column(db.Float, nullable=False, default=0.0) # Total de la TVA collectée
    mode_paiement = db.Column(db.String(30), nullable=False, default="Espèces") 
    
    # Clés étrangères et Relations
    caissier_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True)
    details = db.relationship('DetailVente', backref='vente', lazy=True)

    # --- PONT DE COMPATIBILITÉ : MODE / METHODE PAIEMENT ---
    @property
    def methode_paiement(self):
        """Permet d'utiliser vente.methode_paiement dans les requêtes et scripts JSON."""
        return self.mode_paiement

    @methode_paiement.setter
    def methode_paiement(self, value):
        self.mode_paiement = value


class DetailVente(db.Model):
    __tablename__ = 'details_ventes'
    
    id = db.Column(db.Integer, primary_key=True)
    vente_id = db.Column(db.Integer, db.ForeignKey('ventes.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False) 
    prix_unitaire = db.Column(db.Float, nullable=False) # Prix TTC final facturé
    taux_tva_applique = db.Column(db.Float, nullable=False, default=18.0)