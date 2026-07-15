from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.decorators import role_required
from app import db
from datetime import date, timedelta, datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload
import random
import time

# Importation des modèles et formulaires
from app.models import Utilisateur, Produit, Fournisseur, Vente, DetailVente, Categorie
from werkzeug.security import check_password_hash
from .forms import InscriptionForm, LoginForm 

main = Blueprint('main', __name__) 


@main.route('/')
def accueil():
    return render_template('accueil.html')


@main.route('/inscription', methods=['GET', 'POST'])
def inscription(): 
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('main.vente'))
        
    form = InscriptionForm()
    if form.validate_on_submit():
        user_existe = Utilisateur.query.filter_by(email=form.email.data).first()
        if user_existe:
            flash("Cet email existe déjà !", "danger")
            return redirect(url_for('main.login'))
        
        # CORRECTION : Le rôle est désormais attribué d'office à "vendeur" en arrière-plan
        nouveau_user = Utilisateur(
            nom_utilisateur=form.nom.data, 
            email=form.email.data, 
            role='vendeur'
        )
        nouveau_user.set_password(form.mot_de_passe.data) 
        
        db.session.add(nouveau_user)
        db.session.commit()
        
        flash("Inscription réussie ! Vous pouvez vous connecter.", "success")
        return redirect(url_for('main.login'))
    
    return render_template('inscription.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('main.vente'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = Utilisateur.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.mot_de_passe, form.mot_de_passe.data):
            login_user(user)
            flash("Connexion réussie !", "success")
            
            if user.role == "admin":
                return redirect(url_for("main.dashboard"))
            else:
                return redirect(url_for("main.vente"))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
            
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('main.accueil'))


from datetime import date, timedelta
from app.models import Produit

@main.context_processor
def inject_notifications():
    alertes = []
    today = date.today()
    seuil_alerte_date = today + timedelta(days=15)

    # 1. Alerte Rupture de stock (Stock <= 0)
    ruptures = Produit.query.filter(Produit.stock <= 0).all()
    for p in ruptures:
        alertes.append({
            "niveau": "critique",
            "titre": "Rupture de stock",
            "message": f"Le produit '{p.nom}' est en rupture totale."
        })

    # 2. Alerte Péremption proche (Expire dans les 15 prochains jours)
    proches_peremption = Produit.query.filter(
        Produit.date_peremption.isnot(None),
        Produit.date_peremption <= seuil_alerte_date,
        Produit.date_peremption >= today
    ).count()

    if proches_peremption > 0:
        alertes.append({
            "niveau": "attention",
            "titre": "Péremption proche",
            "message": f"{proches_peremption} article(s) expirent dans moins de 15 jours."
        })

    return dict(alertes=alertes)

# --- NOUVELLE ROUTE : API POUR LA BARRE DE RECHERCHE DYNAMIQUE ---

@main.route('/api/search')
@login_required
def search_api():
    query = request.args.get('q', '').strip()
    results = []

    if not query:
        return jsonify([])

    # 1. Recherche dans les Produits (par nom ou par code-barres)
    matched_products = Produit.query.filter(
        (Produit.nom.ilike(f'%{query}%')) | 
        (Produit.code_barres.ilike(f'%{query}%'))
    ).limit(5).all()

    for p in matched_products:
        results.append({
            'type': 'produit',
            'title': p.nom,
            'subtitle': f"Stock : {p.stock} restant(s)",
            'meta': f"{p.prix_ttc} FCFA",
            'url': url_for('main.produits')  # Renvoie vers la liste des produits
        })

    # 2. Recherche dans les Ventes (par ID/Référence si numérique)
    if query.isdigit():
        matched_sales = Vente.query.filter_by(id=int(query)).limit(3).all()
        for s in matched_sales:
            results.append({
                'type': 'vente',
                'title': f"Facture / Vente n°{s.id}",
                'subtitle': f"Payé par {s.mode_paiement}",
                'meta': f"{s.total} FCFA",
                'url': url_for('main.dashboard')  # Ajuste vers ta route de détails de vente si existante
            })

    return jsonify(results)


# --- PAGES SÉCURISÉES ---

@main.route('/dashboard')
@login_required
@role_required("admin")
def dashboard():
    # 1. KPI D'EN-TÊTE PRINCIPAUX
    ca_total = db.session.query(func.sum(Vente.total)).scalar() or 0

    ventes_today = Vente.query.filter(
        func.date(Vente.date_vente) == date.today()
    ).count()

    total_produits = Produit.query.count()
    total_users = Utilisateur.query.count()

    # 2. ÉVOLUTION DES VENTES (7 derniers jours)
    debut_periode = date.today() - timedelta(days=6)
    ventes_par_jour = db.session.query(
        func.date(Vente.date_vente).label('jour'),
        func.sum(Vente.total).label('total_jour')
    ).filter(
        func.date(Vente.date_vente) >= debut_periode
    ).group_by(
        func.date(Vente.date_vente)
    ).order_by(
        func.date(Vente.date_vente)
    ).all()

    sales_labels = []
    for row in ventes_par_jour:
        if isinstance(row.jour, str):
            try:
                date_obj = datetime.strptime(row.jour, '%Y-%m-%d')
                sales_labels.append(date_obj.strftime('%d/%m'))
            except ValueError:
                sales_labels.append(str(row.jour))
        elif hasattr(row.jour, 'strftime'):
            sales_labels.append(row.jour.strftime('%d/%m'))
        else:
            sales_labels.append(str(row.jour))

    sales_data = [float(row.total_jour) for row in ventes_par_jour]

    # 3. TOP 3 DES PRODUITS LES PLUS VENDUS
    top_produits = db.session.query(
        Produit.nom.label('nom_produit'),
        func.sum(DetailVente.quantite).label('quantite_vendue')
    ).join(
        DetailVente, DetailVente.produit_id == Produit.id
    ).group_by(
        Produit.id
    ).order_by(
        func.sum(DetailVente.quantite).desc()
    ).limit(3).all()

    top_products_labels = [row.nom_produit for row in top_produits]
    top_products_data = [int(row.quantite_vendue) for row in top_produits]

    if not top_products_labels:
        top_products_labels = ["Aucun produit", "Aucun produit", "Aucun produit"]
        top_products_data = [0, 0, 0]

    # 4. ACTIVITÉ RÉCENTE (5 dernières ventes)
    dernieres_ventes = (
        Vente.query
        .options(
            joinedload(Vente.caissier), 
            joinedload(Vente.details).joinedload(DetailVente.produit)
        )
        .order_by(Vente.date_vente.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        ca_total=ca_total,
        ventes_today=ventes_today,
        total_produits=total_produits,
        total_users=total_users,
        sales_labels=sales_labels,
        sales_data=sales_data,
        top_products_labels=top_products_labels,
        top_products_data=top_products_data,
        ventes=dernieres_ventes
    )


# --- GESTION DE LA CAISSE / PANIER ---

@main.route('/vente')
@login_required
def vente():
    liste_produits = Produit.query.all()
    return render_template(
        'vente.html', 
        produits=liste_produits, 
        panier={}, 
        sous_total=0, 
        total=0
    )


# --- API AJAX POUR L'ENCAISSEMENT DYNAMIQUE ---

@main.route('/vente/creer', methods=['POST'])
@login_required
def enregistrer_vente():
    try:
        data = request.get_json()
        if not data or 'panier' not in data:
            return jsonify({'success': False, 'message': 'Le panier est vide ou invalide.'}), 400
        
        panier = data['panier']
        mode_paiement = data.get('mode_paiement', 'Espèces')
        
        if not panier:
            return jsonify({'success': False, 'message': 'Le panier ne contient aucun article.'}), 400
            
        total_vente_ttc = 0.0
        total_tva_vente = 0.0
        details_a_creer = []
        
        for item in panier:
            produit_id = item.get('id')
            quantite = int(item.get('quantite', 1))
            
            produit = Produit.query.get(produit_id)
            if not produit:
                return jsonify({'success': False, 'message': f'Produit {produit_id} introuvable.'}), 404
            
            if produit.stock < quantite:
                return jsonify({
                    'success': False, 
                    'message': f'Stock insuffisant pour "{produit.nom}" (Disponible : {produit.stock}).'
                }), 400
            
            produit.stock -= quantite
            
            prix_unitaire_ttc = produit.prix_ttc
            montant_tva_unitaire = produit.montant_tva_vente
            
            total_vente_ttc += prix_unitaire_ttc * quantite
            total_tva_vente += montant_tva_unitaire * quantite
            
            detail = DetailVente(
                produit_id=produit.id,
                quantite=quantite,
                prix_unitaire=prix_unitaire_ttc,
                taux_tva_applique=produit.taux_tva
            )
            details_a_creer.append(detail)
            
        nouvelle_vente = Vente(
            total=round(total_vente_ttc, 2),
            total_tva=round(total_tva_vente, 2),
            mode_paiement=mode_paiement,
            caissier_id=current_user.id
        )
        
        db.session.add(nouvelle_vente)
        db.session.flush()
        
        for detail in details_a_creer:
            detail.vente_id = nouvelle_vente.id
            db.session.add(detail)
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Vente enregistrée avec succès !', 'vente_id': nouvelle_vente.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Une erreur est survenue : {str(e)}'}), 500


@main.route('/vente/creer_alternative', methods=['POST'])
@login_required
def creer_vente():
    donnees = request.get_json()
    if not donnees or 'items' not in donnees:
        return jsonify({'message': 'Le panier est vide ou invalide.'}), 400
    
    try:
        nouvelle_vente = Vente(
            caissier_id=current_user.id,
            mode_paiement=donnees.get('methode_paiement', 'Espèces'),
            total=0 
        )
        db.session.add(nouvelle_vente)
        db.session.flush() 
        
        total_calcule = 0
        
        for item in donnees['items']:
            if str(item['produit_id']).startswith('fav-'):
                produit = Produit.query.filter_by(nom=item['nom']).first()
            else:
                produit = Produit.query.get(item['produit_id'])
                
            if not produit:
                return jsonify({'message': f"Le produit '{item['nom']}' n'existe pas en base de données."}), 404
            
            if produit.stock < item['quantite']:
                return jsonify({'message': f"Stock insuffisant pour le produit '{produit.nom}'."}), 400
            
            produit.stock -= item['quantite']
            
            detail = DetailVente(
                vente_id=nouvelle_vente.id,
                produit_id=produit.id,
                quantite=item['quantite'],
                prix_unitaire=item['prix_unitaire']
            )
            db.session.add(detail)
            total_calcule += item['quantite'] * item['prix_unitaire']
        
        nouvelle_vente.total = total_calcule
        db.session.commit()
        
        return jsonify({'message': 'Vente enregistrée avec succès !', 'vente_id': nouvelle_vente.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Une erreur est survenue lors de la transaction.', 'erreur': str(e)}), 500


# --- GESTION DES PRODUITS ---

@main.route('/produits', methods=['GET', 'POST'])
@login_required
def produits():
    if request.method == 'POST':
        if current_user.role != "admin":
            flash("Action non autorisée. Seuls les administrateurs peuvent ajouter des produits.", "danger")
            return redirect(url_for('main.produits'))

        nom = request.form.get('nom')
        prix_achat = request.form.get('prix_achat')
        prix_vente = request.form.get('prix_vente')
        stock = request.form.get('stock')
        categorie_id = request.form.get('categorie_id')
        fournisseur_id = request.form.get('fournisseur_id')
        tva = request.form.get('tva')
        date_peremption_str = request.form.get('date_peremption')

        if not nom or not prix_achat or not prix_vente or not stock or not categorie_id or not fournisseur_id:
            flash("Veuillez remplir tous les champs obligatoires (*).", "danger")
            return redirect(url_for('main.produits'))

        try:
            prix_achat = float(prix_achat)
            prix_vente = float(prix_vente)
            stock = int(stock)
            categorie_id = int(categorie_id)
            fournisseur_id = int(fournisseur_id)
            tva = float(tva) if tva else 0.0

            date_peremption = None
            if date_peremption_str:
                date_peremption = datetime.strptime(date_peremption_str, '%Y-%m-%d').date()

            while True:
                prefixe_temps = str(int(time.time()))
                suffixe_aleatoire = str(random.randint(100, 999))
                code_genere = prefixe_temps + suffixe_aleatoire
                if not Produit.query.filter_by(code_barres=code_genere).first():
                    code_barres = code_genere
                    break

            nouveau_produit = Produit(
                nom=nom,
                code_barres=code_barres,
                prix_achat=prix_achat,
                prix_ttc=prix_vente,
                stock=stock,
                categorie_id=categorie_id,
                fournisseur_id=fournisseur_id,
                taux_tva=tva,
                date_peremption=date_peremption
            )
                    
            db.session.add(nouveau_produit)
            db.session.commit()
            flash(f"Le produit '{nom}' a été intégré avec succès !", "success")
            
        except ValueError:
            flash("Erreur de format dans les valeurs numériques ou de date.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur système est survenue : {str(e)}", "danger")

        return redirect(url_for('main.produits'))

    liste_produits = Produit.query.all()
    liste_categories = Categorie.query.all()
    liste_fournisseurs = Fournisseur.query.all()
    
    return render_template(
        'produits.html', 
        liste_produits=liste_produits,
        categories=liste_categories,
        fournisseurs=liste_fournisseurs
    )


# --- GESTION DES AGENTS / COMPTES ---

@main.route('/utilisateurs', methods=['GET', 'POST'])
@login_required
@role_required("admin")
def utilisateurs():
    if request.method == 'POST':
        nom = request.form.get('nom_utilisateur')
        role = request.form.get('role')
        password = request.form.get('mot_de_passe')
        
        if not nom or not password:
            flash("Veuillez remplir tous les champs du formulaire.", "danger")
            return redirect(url_for('main.utilisateurs'))
            
        email = f"{nom.lower().replace(' ', '')}@smartcaisse.com" 
        
        if Utilisateur.query.filter_by(nom_utilisateur=nom).first():
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
        else:
            nouvel_agent = Utilisateur(
                nom_utilisateur=nom,
                email=email,
                role=role.lower().strip() if role else "vendeur"
            )
            nouvel_agent.set_password(password)
            
            db.session.add(nouvel_agent)
            db.session.commit()
            flash(f"L'agent {nom} a été enregistré avec succès !", "success")
            return redirect(url_for('main.utilisateurs'))

    liste_users = Utilisateur.query.all()
    return render_template('utilisateurs.html', utilisateurs=liste_users)


@main.route('/utilisateurs/supprimer/<int:user_id>')
@login_required
@role_required("admin")
def supprimer_utilisateur(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte !", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"L'accès de l'utilisateur {user.nom_utilisateur} a été révoqué.", "success")
    return redirect(url_for('main.utilisateurs'))


# --- GESTION DES FOURNISSEURS ---

@main.route('/fournisseurs', methods=['GET'])
@login_required
def fournisseurs():
    liste_fournisseurs = Fournisseur.query.all()
    SEUIL_ALERTE = 5
    livraisons_en_attente = Produit.query.filter(Produit.stock <= SEUIL_ALERTE).count()
    total_dettes = 0

    return render_template(
        'fournisseurs.html', 
        fournisseurs=liste_fournisseurs,
        livraisons_en_attente=livraisons_en_attente,
        total_dettes=total_dettes
    )


@main.route('/fournisseurs/enregistrer', methods=['POST'])
@login_required
def enregistrer_fournisseur():
    fournisseur_id = request.form.get('fournisseur_id')
    nom = request.form.get('nom')
    email = request.form.get('contact')
    telephone = request.form.get('telephone')
    adresse = request.form.get('adresse')

    if not telephone:
        telephone = "Non renseigné"

    if fournisseur_id:
        fournisseur = Fournisseur.query.get_or_404(fournisseur_id)
        fournisseur.nom = nom
        fournisseur.email = email
        fournisseur.telephone = telephone
        fournisseur.adresse = adresse
        flash("Fournisseur mis à jour avec succès !", "success")
    else:
        nouveau_fournisseur = Fournisseur(
            nom=nom,
            email=email,
            telephone=telephone,
            adresse=adresse
        )
        db.session.add(nouveau_fournisseur)
        flash("Fournisseur ajouté avec succès !", "success")

    db.session.commit()
    return redirect(url_for('main.fournisseurs'))


@main.route('/fournisseurs/delete/<int:id>', methods=['GET'])
@login_required
def delete_fournisseur(id):
    fournisseur = Fournisseur.query.get_or_404(id)
    db.session.delete(fournisseur)
    db.session.commit()
    flash("Fournisseur supprimé !", "danger")
    return redirect(url_for('main.fournisseurs'))