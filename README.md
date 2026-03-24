# KICHEFU-CHEFU STORE Backend

Backend marketplace construit avec Django, PostgreSQL et Django REST Framework.

## Fonctionnalites
- Gestion des voitures, telephones, accessoires et biens immobiliers.
- Gestion des images pour voitures, telephones, immobilier et propositions clients.
- Formulaire API "Vendre avec nous" via le modele `Proposal`.
- Admin Django complet: ajout, modification, suppression, gestion des images.
- Import massif des voitures via CSV dans l'admin (jusqu'a 1000+ annonces).
- API REST avec pagination, filtres, recherche et tri.
- Lien WhatsApp automatique par produit.

## Import CSV massif des voitures (Admin)
1. Aller dans `Admin > Cars > Importer CSV`.
2. Charger un fichier CSV avec les colonnes obligatoires:
	- `marque` / `brand`
	- `modele` / `model`
	- `annee` / `year`
	- `kilometrage` / `mileage`
	- `prix` / `price`
	- `description`
	- `image`
3. Optionnel: charger une archive ZIP d'images.
4. La colonne `image` accepte plusieurs images par voiture (`|`, `;` ou `,`):
	- exemple: `prado-1.jpg|prado-2.jpg|prado-3.jpg`
5. Choisir la strategie de doublon:
	- `Ignorer les doublons`
	- `Mettre a jour les doublons`

Le systeme cree automatiquement les fiches voitures, ajoute les images, et met a jour les pages produits.

## Installation
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Configuration
1. Copier `.env.example` vers `.env`.
2. Adapter vos variables PostgreSQL.

## Migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Lancer le serveur
```bash
python manage.py runserver
```

## Mettre le site en public (Render)
1. Poussez ce projet sur GitHub.
2. Connectez le repo a Render.
3. Render detectera `render.yaml` automatiquement.
4. Lancez le deploy; une URL publique sera creee.
5. Mettez a jour, si besoin, les variables `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` avec votre domaine final.

## API
Base: `/api/marketplace/`

- `cars/`
- `car-images/`
- `phones/`
- `phone-images/`
- `accessories/`
- `real-estate/`
- `real-estate-images/`
- `proposals/`
- `proposal-images/`

## Authentification et securite
- Produits: lecture publique, ecriture reservee aux utilisateurs authentifies.
- Propositions: creation publique, lecture/detail reservee au staff.

### Connexion via numero de telephone
- Identifiant = `username` = numero (ex: `+24381...`).
- Le formulaire d'inscription demande numero + nom complet + mot de passe.
- Le nom complet est utilise uniquement pour l'affichage public (profil / annonces).
- Pour se connecter: renseigner le meme numero + mot de passe (#pas d'adresse e-mail).

> Astuce: sur mobile, le champ numero active le clavier telephonique (attribut `inputmode="tel"`).

## Message WhatsApp
`Bonjour, je suis interesse par ce produit sur KICHEFU-CHEFU STORE.`
