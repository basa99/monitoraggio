# Monitoraggio

Piccola interfaccia web (**Streamlit**) per leggere in modo ordinato l’output dei comandi Linux **`top`** e **`df -h`**, incollato dal terminale.

## Funzionalità

- **Pannello sinistro (`top`)**: incolli il testo prodotto da `top` e ottieni un riepilogo di **RAM** e **swap** (totale e libero in MB se sotto 1 GiB, altrimenti in GB, più percentuale libera) e il **load average** (1, 5 e 15 minuti).
- **Pannello destro (`df -h`)**: incolli l’output di `df -h` e, per i mount **`/data`**, **`/archive`** e **`/backup`** presenti nell’output, vedi dimensione totale e spazio disponibile **nello stesso ordine di grandezza dell’output** (es. `G` → GB, `T` → TB), **con decimali solo se diversi da zero** (es. `1.3T` → 1.3TB, `100G` → 100GB), e la percentuale di utilizzo (**Use%**).

Le due sezioni sono affiancate sulla stessa pagina, separate da una linea verticale.

Supportati i formati tipici di **procps-ng** (`MiB Mem`, ecc.) e il formato classico con suffissi `k`/`m`/ecc.

## Requisiti

- Python 3.10 o superiore (consigliato 3.11+).

## Avvio con ambiente virtuale (venv)

Dal terminale, nella cartella del progetto:

### Windows (PowerShell)

```powershell
cd path\to\monitoraggio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Se l’attivazione del venv è bloccata dalle policy di esecuzione, puoi usare `cmd`:

```cmd
cd path\to\monitoraggio
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m streamlit run app.py
```

### Linux / macOS

```bash
cd path/to/monitoraggio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Il browser si apre di solito su `http://localhost:8501`. Per chiudere l’app, interrompi il processo nel terminale (`Ctrl+C`). Per uscire dal venv: `deactivate`.

La cartella `.venv` è locale alla macchina: non va committata se il team usa `.gitignore` standard per i virtualenv.
