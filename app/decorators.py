from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(role_autorise):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Si l'utilisateur n'est pas connecté, on l'envoie au login
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            
            # 2. S'il est connecté mais n'a pas le bon rôle
            if current_user.role != role_autorise:
                flash("Accès refusé : vous n'avez pas les permissions pour cette section.", "danger")
                
                # FIX SÉCURITÉ : Au lieu de renvoyer vers le login (ce qui fait boucler), 
                # on le redirige vers SA page dédiée.
                if current_user.role == "admin":
                    return redirect(url_for('main.dashboard'))
                else:
                    return redirect(url_for('main.vente')) # Le vendeur reste dans son espace vente !
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator