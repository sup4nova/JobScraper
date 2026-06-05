"""
Modèle de données pour une offre d'emploi
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Offre:
    # Infos principales
    titre: str
    entreprise: str
    ville: str
    lien: str
    source: str  # "indeed" | "linkedin" | "wttj"

    # Infos optionnelles selon le site
    salaire: Optional[str] = None
    niveau_etude: Optional[str] = None
    type_contrat: Optional[str] = None        # CDI, CDD, Stage...
    teletravail: Optional[str] = None
    description: Optional[str] = None
    competences: list = field(default_factory=list)
    date_publication: Optional[str] = None

    def afficher_resume(self, index: int):
        """Affiche un résumé lisible dans le terminal"""
        print(f"\n{'─'*55}")
        print(f"  [{index}] {self.titre} — {self.entreprise}")
        print(f"  📍 {self.ville}   🌐 {self.source.upper()}")
        if self.salaire:
            print(f"  💶 {self.salaire}")
        if self.type_contrat:
            print(f"  📄 {self.type_contrat}")
        if self.niveau_etude:
            print(f"  🎓 {self.niveau_etude}")
        if self.teletravail:
            print(f"  🏠 {self.teletravail}")
        if self.description:
            extrait = self.description[:200].replace('\n', ' ')
            print(f"  📝 {extrait}...")
        print(f"  🔗 {self.lien}")