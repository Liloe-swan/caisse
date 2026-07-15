from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class InscriptionForm(FlaskForm):
    nom = StringField(
        "Nom",
        validators=[DataRequired(), Length(min=2, max=50)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    mot_de_passe = PasswordField(
        "Mot de passe",
        validators=[DataRequired(), Length(min=6)]
    )

    # Le rôle a été retiré d'ici pour laisser ton fichier de routes 
    # attribuer automatiquement le rôle 'vendeur' en arrière-plan.

    submit = SubmitField("Créer mon compte")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    mot_de_passe = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Se connecter")