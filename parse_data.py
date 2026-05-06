import pandas as pd
from bs4 import BeautifulSoup

def nettoyer_encoding(texte):
    if not isinstance(texte, str):
        return ""
    try:
        return texte.encode("latin-1").decode("utf-8")
    except:
        return texte

def nettoyer_texte(soup_elem):
    if not soup_elem:
        return ""
    return nettoyer_encoding(soup_elem.get_text(separator=" ", strip=True))

def extraire_section(soup, nom_ancre):
    ancre = soup.find("a", {"name": nom_ancre})
    if not ancre:
        return ""
    textes = []
    for elem in ancre.find_all_next(["p", "ul", "li"]):
        if elem.find("a", {"name": True}):
            break
        texte = nettoyer_encoding(elem.get_text(separator=" ", strip=True))
        if texte:
            textes.append(texte)
    return " ".join(textes[:10])

def extraire_notice(html):
    if not isinstance(html, str):
        return {}
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Denomination
    denomination = ""
    for ancre_name in ["RcpDenomination", "_Toc142278913"]:
        tag = soup.find("a", {"name": ancre_name})
        if tag:
            p = tag.find_parent("p")
            if p:
                denomination = nettoyer_encoding(p.get_text(strip=True))
                break
    if not denomination:
        for classe in ["AmmDenomination", "AmmCorpsTexteGras"]:
            tag = soup.find("p", class_=classe)
            if tag:
                denomination = nettoyer_encoding(tag.get_text(strip=True))
                break

    # Date mise à jour
    date_maj = ""
    tag_date = soup.find("a", {"name": "RcpDateRevision"})
    if tag_date:
        p = tag_date.find_next("p")
        if p:
            date_maj = nettoyer_encoding(p.get_text(strip=True))

    # Composition
    composition = extraire_section(soup, "RcpComposition")

    # Forme pharmaceutique
    forme = extraire_section(soup, "RcpFormePharm")

    # Titulaire AMM
    titulaire = ""
    tag_titulaire = soup.find("a", {"name": "RcpTitulaireAmm"})
    if tag_titulaire:
        p = tag_titulaire.find_next("p")
        if p:
            titulaire = nettoyer_encoding(p.get_text(strip=True))

    # Numéro AMM
    numero_amm = extraire_section(soup, "RcpNumAutor")

    # Durée conservation
    duree_conservation = extraire_section(soup, "RcpDureeConservation")

    # Excipients
    excipients = extraire_section(soup, "RcpListeExcipients")

    # Surdosage
    surdosage = extraire_section(soup, "RcpSurdosage")

    # Mises en garde
    mises_en_garde = extraire_section(soup, "RcpMisesEnGarde")

    return {
        "denomination":           denomination,
        "date_mise_a_jour":       date_maj,
        "composition":            composition,
        "forme_pharmaceutique":   forme,
        "indications":            extraire_section(soup, "RcpIndicTherap"),
        "posologie":              extraire_section(soup, "RcpPosologie"),
        "contre_indications":     extraire_section(soup, "RcpContreIndications"),
        "mises_en_garde":         mises_en_garde,
        "interactions":           extraire_section(soup, "RcpInteractions"),
        "grossesse_allaitement":  extraire_section(soup, "RcpFertiliteGrossesse"),
        "effets_indesirables":    extraire_section(soup, "RcpEffetsIndesirables"),
        "surdosage":              surdosage,
        "excipients":             excipients,
        "duree_conservation":     duree_conservation,
        "titulaire_amm":          titulaire,
        "numero_amm":             numero_amm,
        "conditions_prescription": extraire_section(soup, "RcpCondPrescription"),
    }

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("📂 Chargement du CSV...")
    df_raw = pd.read_csv(
        "data/CIS_RCP.csv",
        sep="\t",
        encoding="latin-1",
        header=0,
        names=["code_cis", "html_notice"]
    )
    print(f"   {len(df_raw)} notices au total")

    print("\n🔍 Extraction des sections...")
    sections = df_raw["html_notice"].apply(extraire_notice)
    df_sections = pd.DataFrame(sections.tolist())

    df_final = pd.concat([df_raw[["code_cis"]], df_sections], axis=1)

    # Supprimer les lignes sans dénomination
    df_final = df_final[df_final["denomination"].str.len() > 0]
    print(f"   {len(df_final)} notices avec dénomination")

    print("\n💾 Export Excel...")
    df_final.to_excel("data/cisdata.xlsx", index=False)
    print("✅ Fichier exporté : data/cisdata.xlsx")
    
    print("\n--- Aperçu colonnes ---")
    print(df_final.columns.tolist())
    print("\n--- Aperçu données ---")
    print(df_final[["code_cis", "denomination", "conditions_prescription"]].head(5).to_string())