"""
Interface CLI pour sélectionner les offres qui plaisent
"""
from models import Offre


def select_jobs(offres: list[Offre]) -> list[Offre]:
    """Affiche les offres et permet à l'utilisateur d'en sélectionner"""

    print("\n" + "="*55)
    print("  SÉLECTION DES OFFRES")
    print("  (entrez les numéros qui vous intéressent)")
    print("="*55)

    for i, offre in enumerate(offres, start=1):
        offre.afficher_resume(i)

    print(f"\n{'─'*55}")
    print("Commandes :")
    print("  • Numéros séparés par virgule : 1,3,5")
    print("  • Plage : 1-5")
    print("  • Tout sélectionner : all")
    print("  • Quitter sans sélectionner : q")
    print(f"{'─'*55}")

    while True:
        choix = input("\nVotre sélection : ").strip().lower()

        if choix == "q":
            return []

        if choix == "all":
            print(f"✅ {len(offres)} offres sélectionnées.")
            return offres

        indices = _parser_selection(choix, len(offres))

        if indices is None:
            print("⚠️  Format invalide. Exemple valide : 1,3,5 ou 2-7")
            continue

        if not indices:
            print("⚠️  Aucun numéro valide. Réessaie.")
            continue

        selectionnees = [offres[i - 1] for i in indices]
        print(f"\n✅ {len(selectionnees)} offre(s) sélectionnée(s) :")
        for o in selectionnees:
            print(f"   • {o.titre} — {o.entreprise} ({o.source})")

        confirm = input("\nConfirmer et générer les CVs ? [O/n] : ").strip().lower()
        if confirm in ("", "o", "oui", "y", "yes"):
            return selectionnees
        else:
            print("Retour à la sélection...")


def _parser_selection(texte: str, max_index: int) -> list[int] | None:
    """Parse '1,3,5' ou '2-7' en liste d'indices valides"""
    indices = set()

    parties = texte.split(",")
    for partie in parties:
        partie = partie.strip()
        if "-" in partie:
            bornes = partie.split("-")
            if len(bornes) != 2:
                return None
            try:
                debut, fin = int(bornes[0]), int(bornes[1])
                indices.update(range(debut, fin + 1))
            except ValueError:
                return None
        else:
            try:
                indices.add(int(partie))
            except ValueError:
                return None

    # Filtrer les indices hors bornes
    indices_valides = [i for i in sorted(indices) if 1 <= i <= max_index]
    return indices_valides