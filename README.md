# KICHEFU-CHEFU STORE Backend

Backend marketplace construit avec Django, PostgreSQL et Django REST Framework.

## Fonctionnalites
- Gestion des voitures, telephones, accessoires et biens immobiliers.
- Gestion des images pour voitures, telephones, immobilier et propositions clients.
- Formulaire API "Vendre avec nous" via le modele `Proposal`.
- Admin Django complet: ajout, modification, suppression, gestion des images.
- API REST avec pagination, filtres, recherche et tri.
- Lien WhatsApp automatique par produit.

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

## Message WhatsApp
`Bonjour, je suis interesse par ce produit sur KICHEFU-CHEFU STORE.`
