import calendar
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


def is_time_string(turno):
    """Controlla se la stringa è un orario valido nel formato HH:MM o un intervallo HH:MM - HH:MM."""
    try:
        if ' - ' in turno:  # Se è un intervallo
            start_time, end_time = turno.split(' - ')
            h1, m1 = map(int, start_time.split(':'))
            h2, m2 = map(int, end_time.split(':'))
            return 0 <= h1 < 24 and 0 <= m1 < 60 and 0 <= h2 < 24 and 0 <= m2 < 60
        else:  # Se è un orario singolo
            h, m = map(int, turno.split(':'))
            return 0 <= h < 24 and 0 <= m < 60
    except ValueError:
        return False


def calcola_ore_giornata(turni):
    """Calcola il numero totale di ore da una lista di turni, gestendo i casi che attraversano la mezzanotte."""
    ore_turni = 0
    for turno in turni:
        start, end = turno.split(' - ')
        start_h, start_m = map(int, start.split(':'))
        end_h, end_m = map(int, end.split(':'))

        # Gestione del caso in cui il turno attraversa la mezzanotte
        if end_h < start_h or (end_h == start_h and end_m < start_m):
            end_h += 24  # Aggiungi 24 ore per il calcolo

        # Calcolo delle ore
        ore_turno = (end_h + end_m / 60) - (start_h + start_m / 60)
        ore_turni += ore_turno

    return ore_turni


def calcola_altezza_riga(table_data, c, altezza_minima=0.5 * cm):
    altezze_righe = []
    for row in table_data:
        max_height = altezza_minima
        for cell in row:
            # Calcola il numero di righe necessarie per il contenuto della cella
            num_righe = len(str(cell).split("\n"))  # Separiamo i turni usando newline
            cell_height = num_righe * (c._fontsize * 1.2)  # Altezza della cella in punti
            max_height = max(max_height, cell_height)
        altezze_righe.append(max_height)
    return altezze_righe



def suddividi_turno(turno):
    """Dividi un turno in base alle fasce orarie."""
    turni_divisi = []
    start_time, end_time = turno.split(' - ')

    # Converti gli orari in ore e minuti
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour, end_minute = map(int, end_time.split(':'))

    # Verifica se il turno attraversa la mezzanotte
    if start_hour > end_hour or (start_hour == end_hour and start_minute > end_minute):
        print("Errore: Il turno non può attraversare la mezzanotte.")
        return turni_divisi

    # Definisci le fasce orarie
    fasce_orarie = [
        (0, 0, 6, 0),   # Sera: 00:00 - 06:00
        (6, 0, 14, 0),  # Mattina: 06:00 - 14:00
        (14, 0, 22, 0), # Pomeriggio: 14:00 - 22:00
        (22, 0, 24, 0)  # Sera: 22:00 - 24:00
    ]

    for fascia in fasce_orarie:
        fascia_start_hour, fascia_start_minute, fascia_end_hour, fascia_end_minute = fascia

        # Converti le fasce orarie in minuti
        slot_start = fascia_start_hour * 60 + fascia_start_minute
        slot_end = fascia_end_hour * 60 + fascia_end_minute
        shift_start = start_hour * 60 + start_minute
        shift_end = end_hour * 60 + end_minute

        # Controlla se il turno si sovrappone alla fascia oraria
        if (shift_start < slot_end) and (shift_end > slot_start):
            # Calcola i nuovi orari di inizio e fine
            nuovo_inizio = max(shift_start, slot_start)
            nuovo_fine = min(shift_end, slot_end)

            turni_divisi.append(f"{nuovo_inizio // 60:02}:{nuovo_inizio % 60:02} - {nuovo_fine // 60:02}:{nuovo_fine % 60:02}")

    return turni_divisi

def crea_tabella(output_path, mese, anno, pattern_settimanale, eccezioni, nome_lavoratore, persona_assistita, comune,
                 attivita, servizio):
    # Lista dei nomi dei mesi
    mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    # Converti attivita in codice
    codice_servizio = attivita.split(":")[0].strip()


    # Converti il numero del mese in stringa
    mese_stringa = mesi[mese - 1]  # sottrai 1 per l'indice zero

    # Crea un canvas per il PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    larghezza_pagina, altezza_pagina = A4

    # Aggiungi un'immagine tra il titolo e il bordo sinistro con le dimensioni originali
    image_path = "pictures/img1.jpg"
    larghezza_immagine = 102
    altezza_immagine = 60
    x_immagine = 1.5 * cm
    y_immagine = altezza_pagina - altezza_immagine - 0.5 * cm
    c.drawImage(image_path, x_immagine, y_immagine, larghezza_immagine, altezza_immagine)

    # Aggiungi un'intestazione centrata per "SCHEDA ORARIA OPERATORI"
    c.setFont("Helvetica-Bold", 13)
    titolo = "SCHEDA ORARIA OPERATORI"
    larghezza_titolo = c.stringWidth(titolo, "Helvetica-Bold", 13)
    c.drawString((larghezza_pagina - larghezza_titolo) / 2, altezza_pagina - 1.5 * cm, titolo)

    # Aggiungi "Rev.1 del 22/02/2022" centrato tra il titolo e il bordo destro
    c.setFont("Helvetica", 10)
    sottotitolo = "Rev.1 del 22/02/2022"
    larghezza_sottotitolo = c.stringWidth(sottotitolo, "Helvetica", 10)
    spazio_destro = (larghezza_pagina - larghezza_titolo) / 2.5
    posizione_sottotitolo = larghezza_pagina - spazio_destro / 2 - larghezza_sottotitolo / 2
    c.drawString(posizione_sottotitolo, altezza_pagina - 1.5 * cm, sottotitolo)

    # Campi precompilati
    c.drawString(1 * cm, altezza_pagina - 3.2 * cm, f"Nome lavoratrice/tore: {nome_lavoratore}")
    c.drawString(13 * cm, altezza_pagina - 3.2 * cm, f"Persona assistita: {persona_assistita}")
    c.drawString(1 * cm, altezza_pagina - 3.8 * cm, f"Comune: {comune}")
    c.drawString(13 * cm, altezza_pagina - 3.8* cm, f"Servizio: {servizio}")

    # Dati del mese e anno
    c.drawString(1 * cm, altezza_pagina - 4.4 * cm, f"Prestazione: Operatore Socio Sanitario")
    c.drawString(13 * cm, altezza_pagina - 4.4 * cm, f"Mese/Anno: {mese_stringa}/{anno}")

    # Definisci i titoli delle colonne
    titoli_colonne = ["Data/Giorno", "Mattina", "Pomeriggio", "Sera", "Ore", "COD", "Attività", "F.Operatore", "F.Utente"]

    # Usa il modulo 'calendar' per ottenere i giorni del mese
    giorni_del_mese = calendar.monthrange(anno, mese)[1]
    nome_giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

    # Inizia a costruire i dati della tabella
    table_data = [titoli_colonne]

    # Variabile per accumulare le ore mensili
    ore_mensili = 0

    for giorno in range(1, giorni_del_mese + 1):
        giorno_della_settimana = calendar.weekday(anno, mese, giorno)
        nome_giorno = nome_giorni[giorno_della_settimana]

        # Unisci la data e il giorno in un unico campo "Giorno/Data"
        giorno_data = f"{giorno}/{nome_giorno}"

        # Inizializza le variabili per i turni
        turni_mat = []
        turni_pom = []
        turni_sera = []
        codice_eccezione = ""

        # Verifica se il giorno ha un'eccezione
        if giorno in eccezioni:
            orari = eccezioni[giorno]

            # Se ci sono turni, distribuisci in base all'orario
            for turno in orari:  # Considera tutti i turni
                if is_time_string(turno):  # Controlla se il turno è un orario valido
                    turni_divisi = suddividi_turno(turno)
                    for t in turni_divisi:
                        if "06:00" <= t.split(' - ')[0] < "14:00":
                            turni_mat.append(t)
                        elif "14:00" <= t.split(' - ')[0] < "21:00":
                            turni_pom.append(t)
                        elif "21:00" <= t.split(' - ')[0] or (t.split(' - ')[0] < "06:00"):
                            turni_sera.append(t)
                else:
                    codice_eccezione = turno.split(":")[0].strip()  # Salva il codice di eccezione se non è un orario

        else:
            # Usa il pattern settimanale per i giorni senza eccezioni
            orari = pattern_settimanale.get(giorno_della_settimana, [])

            # Distribuisci i turni dal pattern settimanale nelle colonne appropriate
            for turno in orari:  # Considera tutti i turni
                if is_time_string(turno):  # Verifica che il turno sia un orario
                    turni_divisi = suddividi_turno(turno)
                    for t in turni_divisi:
                        if "06:00" <= t.split(' - ')[0] < "14:00":
                            turni_mat.append(t)
                        elif "14:00" <= t.split(' - ')[0] < "21:00":
                            turni_pom.append(t)
                        elif "21:00" <= t.split(' - ')[0] or (t.split(' - ')[0] < "06:00"):
                            turni_sera.append(t)

        # Calcola le ore totali per il giorno
        ore_giornata = calcola_ore_giornata(turni_mat + turni_pom + turni_sera)
        ore_mensili += ore_giornata  # Aggiungi le ore del giorno al totale mensile

        # Aggiungi i dati alla tabella
        table_data.append([
            giorno_data,
            "\n".join(turni_mat),  # Turni della mattina, separati da newline
            "\n".join(turni_pom),  # Turni del pomeriggio, separati da newline
            "\n".join(turni_sera),  # Turni della sera, separati da newline
            f"{ore_giornata:.2f}",  # Colonna Ore
            codice_eccezione,  # Codice dell'eccezione
            codice_servizio if turni_mat or turni_pom or turni_sera else "",  # Attività se ci sono turni
        ])


    # Calcola le altezze delle righe dopo aver aggiunto i dati
    altezza_righe = calcola_altezza_riga(table_data, c)

    larghezza_colonne = [2.5 * cm, 2.8 * cm, 2.8 * cm, 2.5 * cm, 1 * cm, 1 * cm, 1.5 * cm, 2.2 * cm, 3.2* cm]
    # altezze_righe = [0.45 * cm] * len(table_data)

    # Creazione della tabella
    tabella = Table(table_data, colWidths=larghezza_colonne, rowHeights=altezza_righe)

    # Stile della tabella
    stile_tabella = TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ])
    tabella.setStyle(stile_tabella)

    # Posiziona la tabella
    tabella_x = (larghezza_pagina - sum(larghezza_colonne)) / 2
    tabella_y = altezza_pagina - 21 * cm
    tabella.wrapOn(c, larghezza_pagina, altezza_pagina)
    tabella.drawOn(c, tabella_x, tabella_y)

    # Aggiungi le immagini nella colonna "F.Operatore"
    # Percentuale di riduzione
    percentuale = 0.12  # 12%

    # Dimensioni originali dell'immagine
    larghezza_originale = 509
    altezza_originale = 96

    # Calcola le nuove dimensioni
    larghezza_nuova = larghezza_originale * percentuale
    altezza_nuova = altezza_originale * percentuale

    # Aggiungi le immagini nella colonna "F.Operatore"
    for i in range(1, len(table_data)):  # Inizia da 1 per saltare l'intestazione
        turni_mat = table_data[i][1]  # Turni della mattina
        turni_pom = table_data[i][2]  # Turni del pomeriggio
        turni_sera = table_data[i][3]  # Turni della sera

        # Controlla se ci sono turni lavorati in almeno una delle colonne
        if turni_mat or turni_pom or turni_sera:
            image_path = "pictures/f_porcedda_firma.jpg"  # Percorso dell'immagine nella colonna "F.Operatore"
            if os.path.exists(image_path):
                # Calcola la posizione per l'immagine
                img_x = tabella_x + sum(larghezza_colonne[:7]) + (
                            larghezza_colonne[7] - larghezza_nuova) / 2  # Centra l'immagine nella cella

                # Calcola la posizione verticale (y) per l'immagine
                img_y = tabella_y + altezza_righe[i - 1] * (len(table_data) - i) + (
                            altezza_righe[i - 1] - altezza_nuova) / 2 - altezza_righe[i - 1]

                c.drawImage(image_path, img_x, img_y, width=larghezza_nuova, height=altezza_nuova, mask='auto')

    # Aggiungi la sezione sotto la tabella
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1 * cm, tabella_y - 2 * cm, "Totali ore svolte n. ")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(4.5 * cm, tabella_y - 2 * cm, f"{ore_mensili:.2f}")  # Mostra il totale delle ore mensili

    c.setFont("Helvetica-Bold", 10)
    c.drawString(1 * cm, tabella_y - 4.5 * cm, "Note")
    c.setFont("Helvetica", 9)
    c.setFont("Helvetica", 9)
    c.drawString(2.5 * cm, tabella_y - 4.5 * cm, "______________________")  # Seconda riga
    c.drawString(2.5  * cm, tabella_y - 5 * cm, "______________________")  # Terza riga
    c.drawString(2.5  * cm, tabella_y - 5.5 * cm, "______________________")  # Quarta riga
    c.drawString(2.5  * cm, tabella_y - 6 * cm, "______________________")  # Quinta riga
    c.drawString(2.5  * cm, tabella_y - 6.5 * cm, "______________________")  # Sesta riga

    # Legenda per attività
    c.setFont("Helvetica-Bold", 10)
    x = 12 * cm
    y = tabella_y - 1 * cm
    c.drawString(x, y, "Legenda per attività")

    # Disegna una linea sottostante
    c.line(x, y - 2, x + c.stringWidth("Legenda per attività", "Helvetica-Bold", 10), y - 2)

    c.setFont("Helvetica", 8)
    c.drawString(8 * cm, tabella_y - 1.5 * cm, "A1: igiene personale")
    c.drawString(8 * cm, tabella_y - 2 * cm, "A2: igiene ambiente")
    c.drawString(8 * cm, tabella_y - 2.5 * cm, "A3: accompagnamento/assist. extradomiciliare")
    c.drawString(8 * cm, tabella_y - 3 * cm, "A4: preparazione e/o somministrazione pasti")
    c.drawString(15 * cm, tabella_y - 1.5 * cm, "B1: disbrigo pratiche")
    c.drawString(15 * cm, tabella_y - 2 * cm, "B2: programmazione")
    c.drawString(15 * cm, tabella_y - 2.5 * cm, "C1: aiuto somministrazione terapia")
    c.drawString(15 * cm, tabella_y - 3 * cm, "C2: supporto emotivo/socializzazione")

    # Legenda per codici a destra
    c.setFont("Helvetica-Bold", 10)
    x = 12 * cm
    y = tabella_y - 4.2 * cm
    c.drawString(x, y, "Legenda per codici")

    # Disegna una linea sottostante per simulare la sottolineatura
    c.line(x, y - 2, x + c.stringWidth("Legenda per codici", "Helvetica-Bold", 10), y - 2)

    c.setFont("Helvetica", 8)
    # Font per le legende
    c.drawString(8 * cm, tabella_y - 5 * cm, "PR: Permesso Recupero")
    c.drawString(8 * cm, tabella_y - 5.5 * cm, "FE: Ferie")
    c.drawString(8 * cm, tabella_y - 6 * cm, "R: Recupero")
    c.drawString(8 * cm, tabella_y - 6.5 * cm, "P: Permesso")
    c.drawString(12 * cm, tabella_y - 5 * cm, "ST: Straordinario")
    c.drawString(12 * cm, tabella_y - 5.5 * cm, "MA: Malattia")
    c.drawString(12 * cm, tabella_y - 6 * cm, "LD: Lavoro Domenicale")
    c.drawString(12 * cm, tabella_y - 6.5 * cm, "PN: Permesso NON Retribuito")
    c.drawString(17 * cm, tabella_y - 5 * cm, "PL: Permesso Lutto")
    c.drawString(17 * cm, tabella_y - 5.5 * cm, "VM: Visita Medica")
    c.drawString(17 * cm, tabella_y - 6 * cm, "S: Sostituzione")
    c.drawString(17 * cm, tabella_y - 6.5 * cm, "PAT: Festa Patronale")

    # Aggiungi le immagini sotto la tabella
    altezza_immagine = 40
    immagine_larghezza = 3.5 * cm
    spazio_immagini = (larghezza_pagina - (3 * immagine_larghezza)) / 4

    immagini = ["pictures/img2.jpg", "pictures/img3.png", "pictures/img4.jpg"]
    for i, img in enumerate(immagini):
        x_immagine = spazio_immagini + (i * (immagine_larghezza + spazio_immagini))
        y_immagine = tabella_y - 8.5 * cm
        c.drawImage(img, x_immagine, y_immagine, immagine_larghezza, altezza_immagine, mask='auto')

    # Salva il PDF
    c.save()

    # Apri il PDF generato
    os.system(f"open {output_path}")
