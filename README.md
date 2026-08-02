# SOK Graph Explorer

SOK Graph Explorer je veb-aplikacija za učitavanje, pregled, pretragu i izmenu grafova. Projekat je organizovan kao skup nezavisnih Python komponenti i dodataka (plugin-ova).

## Tim i članovi tima

- Tim: **18 A**
- Član tima: **Petar Prlina**

## Preduslovi

Za pokretanje su potrebni:

- Linux, macOS, WSL ili drugi sistem sa Bash okruženjem;
- Python 3.10 ili noviji;
- Python modul `venv` i `pip`, ili alat `uv`;
- slobodan TCP port 5000 (podrazumevana vrednost).

Verzije se mogu proveriti komandama:

```bash
python3 --version
python3 -m venv --help >/dev/null && echo "venv je dostupan"
```

## Instalacija i pokretanje

Projekat sadrži skripte `SOK_Graph_Project/start.sh` i `SOK_Graph_Project/stop.sh`. Skripta `start.sh` pri prvom pokretanju automatski:

1. kreira virtuelno okruženje u `SOK_Graph_Project/.venv`;
2. instalira API, platformu, aplikaciju i sve ugrađene dodatke u editable režimu;
3. pokreće server u pozadini;
4. čuva PID procesa u `.graph_explorer.pid`, a izlaz servera u `.graph_explorer.log`;
5. proverava da li je aplikacija dostupna.

Iz korena repozitorijuma redom kopirati i izvršiti:

```bash
cd SOK_Graph_Project
chmod +x start.sh stop.sh
./start.sh
```

Posle uspešnog pokretanja aplikacija je dostupna na adresi:

<http://127.0.0.1:5000/>

Ponovljeno izvršavanje `./start.sh` neće pokrenuti još jednu instancu ako je postojeći proces i dalje aktivan.

### Parametrizacija projekta

Podešavanja se zadaju promenljivama okruženja pre komande `./start.sh`:

| Promenljiva | Podrazumevana vrednost | Namena |
|---|---:|---|
| `SOK_GRAPH_HOST` | `127.0.0.1` | Mrežna adresa na kojoj server sluša |
| `SOK_GRAPH_PORT` | `5000` | Port aplikacije |
| `SOK_GRAPH_VENV` | `SOK_Graph_Project/.venv` | Putanja virtuelnog Python okruženja |
| `SOK_GRAPH_DEBUG` | `false` | Uključuje Flask debug režim kada je vrednost `true` |

Primer pokretanja na svim mrežnim interfejsima i portu 8000:

```bash
SOK_GRAPH_HOST=0.0.0.0 SOK_GRAPH_PORT=8000 ./start.sh
```

U tom slučaju lokalna adresa je <http://127.0.0.1:8000/>. Vrednost `0.0.0.0` treba koristiti samo na mreži na kojoj je dozvoljeno da drugi uređaji pristupe aplikaciji.

Za zaustavljanje aplikacije koristi se:

```bash
./stop.sh
```

Skripta čita PID koji je zapisao `start.sh`, uredno prekida baš taj proces i uklanja PID datoteku. Ako aplikacija nije pokrenuta, komanda to prijavljuje i završava se bez greške.

## Provera funkcionalnosti — komande korak po korak

Sledeći blok je namenjen izvršavanju iz **korena repozitorijuma**. Komande se mogu kopirati jedna za drugom:

```bash
cd SOK_Graph_Project
chmod +x start.sh stop.sh
./start.sh
curl -fsS http://127.0.0.1:5000/ >/dev/null && echo "OK: početna stranica je dostupna"
curl -fsS http://127.0.0.1:5000/plugins | .venv/bin/python -m json.tool
.venv/bin/python -m unittest discover -s tests -v
./stop.sh
```

Očekivani rezultat je:

- poruka `Graph Explorer is running` nakon pokretanja;
- poruka `OK: početna stranica je dostupna`;
- JSON odgovor koji navodi dva dodatka za izvor podataka (`csv`, `json`) i dva dodatka za vizuelizaciju (`simple_visualizer`, `block_visualizer`);
- završna poruka testova `OK`;
- poruka `Graph Explorer stopped`.

Ako je izabran drugi port, isti port mora da se navede i u `curl` komandama. Na primer:

```bash
SOK_GRAPH_PORT=8000 ./start.sh
curl -fsS http://127.0.0.1:8000/ >/dev/null && echo "OK"
./stop.sh
```

Log servera može da se pregleda komandom:

```bash
sed -n '1,200p' .graph_explorer.log
```

## Ručna provera kroz korisnički interfejs

1. Pokrenuti aplikaciju komandom `./start.sh` i otvoriti <http://127.0.0.1:5000/>.
2. Izabrati **File → Open**.
3. Kao **Data Source** izabrati CSV ili JSON dodatak.
4. Kao **Visualizer** izabrati Simple Visualizer ili Block Visualizer.
5. Kao **Source Path** izabrati jedan od ponuđenih primera, na primer `plugins/json_data_source/json_data/cyclic_directed.json`.
6. Kliknuti na **Create Workspace**. Graf treba da se pojavi u glavnom prikazu, a njegovo stablo i umanjeni pregled u bočnim panelima.
7. Isprobati pretragu i filtere u alatnoj traci. Prikaz grafa i prikaz stabla treba da se osveže u skladu sa rezultatom.
8. U donjem CLI panelu uneti neku od komandi iz narednog odeljka i kliknuti na **Execute**.
9. Otvoriti **Plugins** i proveriti da li su prikazana četiri instalirana dodatka.
10. Po završetku izvršiti `./stop.sh` u terminalu.

## CLI komande u aplikaciji

CLI polje u donjem delu stranice menja graf aktivnog radnog prostora. Podržane su sledeće komande:

```text
search Alice
filter age>=20
create_node id=50 name=Petar age=22
edit_node id=50 age=23
delete_node id=50
create_edge id=e50 n1=1 n2=2 weight=2.5
edit_edge id=e50 weight=3.25
delete_edge n1=1 n2=2
clear_graph
```

Argumenti komandi za čvorove i grane pišu se u formatu `ključ=vrednost`. Čvor nije moguće obrisati dok učestvuje u nekoj grani. Komanda `clear_graph` prazni graf u aktivnom radnom prostoru.

## Kako aplikacija radi

### Komponente

- `api` definiše zajednički model grafa (`Graph`, `Node`, `Edge`) i interfejse koje dodaci implementiraju.
- `platform` sadrži poslovnu logiku: radne prostore, pretragu i filtere, CLI, prikaz stabla, umanjeni prikaz i otkrivanje dodataka.
- `graph_explorer` je Flask veb-aplikacija koja povezuje korisnički interfejs sa servisima platforme.
- `plugins/csv_data_source` i `plugins/json_data_source` učitavaju grafove iz CSV i JSON podataka.
- `plugins/simple_visualizer` i `plugins/block_visualizer` pretvaraju graf u HTML prikaz.

Dodaci se registruju kao Python entry point-i. Kada se server pokrene, `PluginService` pronalazi instalirane dodatke i razvrstava ih na izvore podataka i vizuelizatore. Zbog editable instalacije promene u lokalnom izvornom kodu se koriste bez ponovne izgradnje paketa; posle izmene Python koda server treba ponovo pokrenuti.

### Tok rada

Korisnik bira izvor podataka, putanju datoteke ili CSV direktorijuma i način vizuelizacije. Aplikacija preko odgovarajućeg data-source dodatka učitava čvorove i grane i od njih pravi radni prostor. Moguće je otvoriti više radnih prostora i prebacivati se između njih.

Aktivni graf se prikazuje istovremeno u glavnom prikazu, stablu i umanjenom prikazu. Pretraga pronalazi čvorove po tekstu, a filter poredi izabrani atribut operatorima `=`, `==`, `!=`, `<`, `<=`, `>` i `>=`. CLI omogućava pretragu, filtriranje i izmene čvorova i grana. Nakon svake operacije server vraća osvežen prikaz klijentu.

Plugin Manager prikazuje instalirane dodatke, omogućava instalaciju dodatka sa lokalne putanje, uklanjanje dodatka i ponovno učitavanje registra dodataka.

Radni prostori i izmene grafa čuvaju se u memoriji procesa. Zaustavljanjem servera gube se otvoreni radni prostori i izmene koje nisu upisane u izvorne CSV/JSON datoteke.

## Struktura repozitorijuma

```text
SOK_Graph_Project/
├── api/                    # Model grafa i javni interfejsi
├── platform/               # Servisi i delovi korisničkog interfejsa
├── graph_explorer/         # Flask aplikacija
├── plugins/                # Izvori podataka i vizuelizatori
├── tests/                  # Regresioni testovi
├── start.sh                # Instalacija (po potrebi) i pokretanje
└── stop.sh                 # Zaustavljanje aplikacije
```
