# Rejtő Jenő Hang- és Karakterdosszié — Auris Hangstúdió

Interaktív, 1920–30-as évekbeli illusztrált kalandregény-stílusú webes karakterdosszié és hangarchívum Rejtő Jenő (P. Howard) regényeihez (*Piszkos Fred, a kapitány*, *Piszkos Fred közbelép*, *Az elveszett cirkáló*).

## Moduláris felépítés (Nulla beégetett szöveg!)

Az alkalmazás 100%-ban adatközpontú és natívan fut **GitHub Pages**-en:

```text
Auris-Cast-Dossier/
├── index.html                        # Tiszta HTML5 váz
├── css/
│   ├── theme-rejto.css               # 1920-30-as évekbeli pergamen & tusrajz dizájn, színpaletta
│   ├── intro.css                     # A főoldali bemutató és az Élő Karakter-Műhely stílusa
│   └── components.css                # Karakterkártyák, szűrők, hanglejátszó, nagyító modal
├── js/
│   ├── app.js                        # Fő vezérlő, dinamikus JSON/MD betöltés (fetch)
│   ├── md-parser.js                  # Markdown feldolgozó (REJTO_CAST_REGISTRY.md & intro_story.md)
│   ├── view-intro.js                 # 1. Fül: Hogyan születnek a hangok? + Élő Karakter-Műhely
│   ├── view-rejto.js                 # 2. Fül: Rejtő Karakterdosszié (59 szereplő)
│   └── view-studio.js                # 3. Fül: Általános Színésztár (46 stúdiószínész)
├── data/
│   ├── intro_story.md                # A főoldal teljes szövege Markdownban (szabadon szerkeszthető!)
│   ├── REJTO_CAST_REGISTRY.md        # SSoT szereplőlista (29 főszereplő + 30 mellékszereplő)
│   ├── rejto_master_database.json    # SSoT mély karakter-, hang-, lélektani és kinézet-adatbázis
│   ├── rejto_assets_manifest.json    # Elérhető portrék, mesterhangok és mini-jelenet szövegkönyvek
│   └── studio_actors.json            # A 46 általános szinkronszínész adatai
├── rejto/                            # Rejtő portrék (.webp), mesterhangok (.wav) és szövegkönyvek (.txt)
└── sync_ssot.py                      # Szinkronizáló szkript az I:\COMMON\XTTS\Voices\Rejto SSoT mappából
```

## Frissítés a központi (SSoT) adatbázisból

Ha az `I:\COMMON\XTTS\Voices\Rejto\` mappában frissül a `rejto_master_database.json`, a `REJTO_CAST_REGISTRY.md`, vagy új portré/hangminta készül, futtasd:

```powershell
python sync_ssot.py
```

Ha a főoldali bevezető szöveget szeretnéd módosítani, egyszerűen szerkeszd a `data/intro_story.md` fájlt!

## Helyi előnézet indítása

Mivel a böngésző `fetch()` hívásokkal olvassa be a `data/` mappában lévő `.json` és `.md` fájlokat, helyi gépen egy egyszerű statikus szerverrel nyisd meg:

```powershell
python -m http.server 8080
```
Majd nyisd meg a `http://localhost:8080` címet a böngészőben.
