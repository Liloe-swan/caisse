import random
from datetime import date, timedelta, datetime
from . import db
from app.models import Utilisateur, Categorie, Fournisseur, Produit, Vente, DetailVente

def seed_database():
    # --- CONDITION DE VÉRIFICATION ---
    # Si un utilisateur existe, on arrête tout : la base est déjà peuplée.
    if Utilisateur.query.first():
        print("✅ La base de données est déjà peuplée. Aucune modification nécessaire.")
        return
    # ----------------------------------

    print("⏳ Initialisation du peuplement de la base de données...")

    # On crée les tables si elles n'existent pas encore
    db.create_all()

    # 2. CRÉATION DES UTILISATEURS
    print("👤 Création des utilisateurs...")
    
    admin = Utilisateur(
        nom_utilisateur="SuperAdmin",
        email="admin@smartcaisse.com",
        role="admin"
    )
    admin.set_password("Admin2026!")
    db.session.add(admin)

    vendeurs_data = [
        ("Moussa Diop", "moussa@smartcaisse.com"),
        ("Awa Ndiaye", "awa@smartcaisse.com"),
        ("Fatou Sow", "fatou@smartcaisse.com")
    ]
    
    vendeurs = []
    for nom, email in vendeurs_data:
        v = Utilisateur(
            nom_utilisateur=nom,
            email=email,
            role="vendeur"
        )
        v.set_password("Vendeur2026!")
        db.session.add(v)
        vendeurs.append(v)

    # 3. CRÉATION DES FOURNISSEURS
    print("🚚 Création des fournisseurs...")
    fournisseurs = [
        Fournisseur(nom="Somone Distribution", telephone="+221 33 824 55 11", email="contact@somone.sn", adresse="Zone Industrielle, Dakar", tva_defaut=18.0),
        Fournisseur(nom="Sodis Alimentaire", telephone="+221 33 865 22 44", email="info@sodis.sn", adresse="Avenue Bourguiba, Dakar", tva_defaut=18.0),
        Fournisseur(nom="Top Logistique", telephone="+221 77 500 11 22", email="toplog@gmail.com", adresse="Rufisque, Dakar", tva_defaut=0.0)
    ]
    for f in fournisseurs:
        db.session.add(f)
    
    # 4. CRÉATION DES CATÉGORIES
    print("🗂️ Création des catégories...")
    categories = {
        "Alimentation": Categorie(nom="Alimentation"),
        "Boissons": Categorie(nom="Boissons"),
        "Entretien & Maison": Categorie(nom="Entretien & Maison"),
        "Hygiène & Beauté": Categorie(nom="Hygiène & Beauté")
    }
    for cat in categories.values():
        db.session.add(cat)

    db.session.flush()

    # 5. CRÉATION DES PRODUITS
    print("📦 Création des produits...")
    produits_bruts = {
        "Alimentation": [
            ["Riz Brisé Parfumé 5kg", 3200, 4500, 45, None],
            ["Huile Végétale 1L", 900, 1300, 0, None],
            ["Sucre en Poudre 1kg", 550, 750, 80, None],
            ["Pâtes Spaghetti 500g", 300, 450, 120, 200],
            ["Lait en Poudre 400g", 1800, 2400, 4, 10],
            ["Café Soluble 200g", 1400, 2100, 25, 180],
            ["Chocolat à tartiner", 1100, 1700, 15, 8],
            ["Biscuits Sablés", 200, 350, 60, -2]
        ],
        "Boissons": [
            ["Eau Minérale 1.5L (Pack de 6)", 1000, 1500, 30, 365],
            ["Jus d'Orange 1L", 700, 1100, 40, 90],
            ["Soda Cannette 33cl", 250, 400, 200, 400],
            ["Boisson Énergisante", 600, 1000, 50, 250],
            ["Sirop de Menthe 75cl", 1200, 1800, 18, None]
        ],
        "Entretien & Maison": [
            ["Lessive Liquide 3L", 3500, 5200, 14, None],
            ["Eau de Javel 1L", 400, 650, 35, None],
            ["Liquide Vaisselle 500ml", 500, 800, 50, None],
            ["Éponge Multi-usages (Lot de 3)", 250, 450, 90, None],
            ["Sac Poubelle 50L (x10)", 700, 1100, 40, None]
        ],
        "Hygiène & Beauté": [
            ["Savon de Toilette 100g", 250, 400, 100, None],
            ["Dentifrice Fluor 75ml", 600, 950, 55, 500],
            ["Shampooing Douceur 400ml", 1300, 2000, 20, None],
            ["Gel Douche Rafraîchissant", 900, 1500, 28, 300],
            ["Déodorant Spray 150ml", 1100, 1800, 22, None]
        ]
    }

    tous_les_produits = []
    for nom_cat, items in produits_bruts.items():
        cat = categories[nom_cat]
        for item in items:
            nom_p, prix_achat, prix_vente_ttc, stock, jours_peremption = item
            code_barres = f"619{random.randint(100000000, 999999999)}"
            date_p = (date.today() + timedelta(days=jours_peremption)) if jours_peremption is not None else None
            
            p = Produit(nom=nom_p, code_barres=code_barres, prix_achat=prix_achat, stock=stock, 
                        taux_tva=18.0, categorie=cat, fournisseur=random.choice(fournisseurs), date_peremption=date_p)
            p.prix_ttc = prix_vente_ttc
            db.session.add(p)
            tous_les_produits.append(p)

    db.session.flush()

    # 6. HISTORIQUE DE VENTES
    print("📊 Génération de l'historique des ventes...")
    modes = ["Espèces", "Carte Bancaire", "Wave", "Orange Money"]
    for i in range(7):
        date_hist = date.today() - timedelta(days=i)
        for _ in range(random.randint(3, 6)):
            v = Vente(caissier=random.choice(vendeurs), mode_paiement=random.choice(modes), total=0.0, total_tva=0.0)
            v.date_vente = datetime.combine(date_hist, datetime.now().time())
            db.session.add(v)
            db.session.flush()
            
            for prod in random.sample(tous_les_produits, random.randint(1, 4)):
                q = random.randint(1, 3)
                db.session.add(DetailVente(vente_id=v.id, produit_id=prod.id, quantite=q, prix_unitaire=prod.prix_ttc, taux_tva_applique=prod.taux_tva))
                v.total += prod.prix_ttc * q
                v.total_tva += prod.montant_tva_vente * q

    db.session.commit()
    print("✅ Base de données initialisée et peuplée avec succès !")