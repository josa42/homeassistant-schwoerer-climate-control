# Design: Schwörer Climate Control

Dieses Dokument hält die Entscheidungen fest, aus denen der Nachfolger von
`schwoerer_wgt_controller` gebaut wird, und die Begründungen dazu. Es ist die
Antwort auf die Frage "warum eigentlich so", die in sechs Monaten genauso wichtig
ist wie "warum ist der Zusatzheizer an".

Repo: `homeassistant-schwoerer-climate-control`, Domain `schwoerer_climate_control`.

## Warum v1 ersetzt wird

Die Symptome waren, dass geschriebene Werte nicht ankamen. Die Ursache liegt im
Schreibpfad, nicht in der Logik.

`schwoerer_lueftung` schreibt ein Feld und löst danach sofort einen vollständigen
Geräte-Poll aus (`coordinator.py`, `async_write`). v1 schrieb pro Zyklus rund 15
Felder: sechs Solltemperaturen, sechs HVAC-Modi, Luftstufe und zwei Schalter.
Jeder dieser Writes zog einen Poll über dieselbe Modbus-Verbindung hinter sich
her. Zusätzlich wertete v1 nicht nur alle 15 Minuten aus, sondern bei jeder
Zustandsänderung jedes beobachteten Fenster-, Feuchte- und CO₂-Sensors, und jede
Auswertung schrieb alle Werte erneut, ohne zu prüfen, ob sie sich geändert hatten.

Zwei weitere Defekte aus v1, die unabhängig davon behoben werden:

`DEFAULT_HEAT_PUMP_CHANGE_LOCKOUT_MINUTES = 30` war in `const.py` definiert und
wurde nirgends benutzt. Die handgeschriebene Automation `automation.heizung`
implementiert diese Sperre, v1 hat sie verloren. Die Freigabe der Wärmepumpe
konnte also an der 16-Grad-Schwelle beliebig oft kippen.

Es gab keine Hysterese. `outdoor_temp < threshold` entscheidet bei einem Wert, der
um die Schwelle pendelt, bei jeder Auswertung neu.

## Umfang

Die Integration steuert eine Schwörer WGT über die Entities von
`schwoerer_lueftung` und kann zusätzlich Räume mitversorgen, die die WGT nicht
heizt. Sie ist bewusst herstellerspezifisch: zentrale Luftstufe für alle Räume,
Wärmepumpenfreigabe mit Kompressorschutz, Zusatzheizer pro Raum über `hvac_mode`,
Betriebsart auf `manual`, Bypass nur lesbar. Keines dieser Konzepte gibt es in
einer generischen Klimasteuerung.

Wiederverwendbar wird sie über die Schichtung, nicht über den Namen. Die Engine
ist herstellerneutral und ohne Home-Assistant-Import, die Gerätekenntnis steckt in
Adaptern. Eine Klimaanlage ist später ein Adapter, kein Umbau.

## Architektur

| Teil | Aufgabe |
| --- | --- |
| `engine.py` | Reine Funktion von (Inputs, Config, Zeit) auf eine Entscheidung. Kein HA-Import, kein Schreiben. |
| `models.py` | `Decision`, `Gate`, `EffectiveConfig`, `Setting`. Jede Einstellung trägt ihren Wert und ihre Herkunft. |
| `adapters/schwoerer.py` | Kennt Luftstufe, Wärmepumpenfreigabe, Zusatzheizer, Heiz-Kühlfunktion, Stoßlüftung. |
| `adapters/generic.py` | Kennt nur eine `climate`-Entity: Solltemperatur und heizen oder aus. |
| `coordinator.py` | Auswertung takten, Diffs bilden, Writes bündeln, Rate-Cap, Entscheidungen veröffentlichen. |

Das Muster ist aus `cover-control` übernommen, wo die Trennung zwischen reiner
Geometrie und Home-Assistant-Anbindung sich bewährt hat.

## Schreibdisziplin

Der Schutz gegen Modbus-Überlastung liegt auf zwei Schichten mit getrennter
Verantwortung. Transportsicherheit gehört zu `schwoerer_lueftung`, weil dort die
Verbindung liegt und weil jeder andere Schreiber davon profitiert, auch die UI und
eigene Skripte. Absichtsdisziplin gehört in den Controller.

In `schwoerer_lueftung` (eigenes Repo, eigener Arbeitsschritt):

| Maßnahme | Grund |
| --- | --- |
| Serialisierte Write-Queue | Nie zwei Writes gleichzeitig auf einer Modbus-Verbindung. |
| Mindestabstand zwischen Writes | Das Gerät braucht Zeit zwischen Registerzugriffen. |
| Coalescing pro Feld | Von drei Writes auf dasselbe Register in einer Sekunde ist nur der letzte interessant. |
| Readback-Verifikation mit Retry | Ein stillschweigend verworfener Write ist genau der Fehler, der v1 unbrauchbar machte. |
| Kein Poll pro Write | Ein Poll nach dem Ende der Queue genügt. |

Im Controller:

| Maßnahme | Grund |
| --- | --- |
| Nur Diffs schreiben | Was schon stimmt, braucht keinen Write. |
| Ein Bündel pro Entscheidung | Nicht pro Regel, nicht pro Raum. |
| Debounce 30 s auf Zustandsänderungen | Ein Fensterkontakt, der prellt, löst eine Auswertung aus, nicht acht. |
| Mindestens 60 s zwischen zwei Bündeln | Obergrenze für die Last, unabhängig davon wie viele Trigger feuern. |
| Zusätzlich alle 15 Minuten | Damit Zeitgrenzen wie die Nachtabsenkung auch ohne Trigger greifen. |

## Bedienmodell

Alles Zentrale hängt am Hub-Gerät. Pro Raum gibt es nur den Entscheidungs-Sensor,
weil die Luftstufe ohnehin zentral ist und punktuelle Eingriffe über die zentralen
Regler laufen.

| Entity | Werte | Bedeutung |
| --- | --- | --- |
| `switch` Aktiv | an, aus | Aus schreibt der Controller keinen einzigen Wert mehr. Die Anlage läuft mit ihren letzten Werten weiter, die Entscheidungs-Sensoren zeigen weiter, was er täte. |
| `switch` Dry-Run | an, aus | Alles wird ausgewertet und veröffentlicht, nichts geschrieben. Beim ersten Setup an. |
| `select` Modus | Heizen, Lüften, Kühlen | Welche Energierichtung erlaubt ist. Nicht, was gerade läuft. |
| `switch` Urlaub | an, aus | Modifikator auf den Modus, keine eigene Betriebsart. |
| `select` Lüfter | automatic, quiet, boost, 0 bis 4 | Modi und feste Stufen in einem Select, so wie das Geräte-Select es auch aufbaut. |
| `sensor` Entscheidung (Hub) | Absicht | Zentrale Entscheidung mit allen Inputs, Gates und Einstellungen als Attribute. |
| `sensor` Entscheidung (pro Raum) | Absicht | Dasselbe für einen Raum. |
| `binary_sensor` Eingeschränkt | an, aus | Mindestens eine konfigurierte Eingabe fehlt. |

Die Betriebsart des Geräts bleibt auf `manual` und wird nur gelesen. Steht sie
anders, meldet der Controller das als Repair und arbeitet nicht dagegen. Zwei
Automatiken, die sich gegenseitig überschreiben, sind der Grund, warum "warum ist
X an" unbeantwortbar wird.

## Modus als Energierichtung

Der Modus heißt nicht Sommer und Winter, sondern Heizen, Lüften und Kühlen. Das
hat drei Konsequenzen, die alle gewollt sind.

Der Name sagt, welches Gate offen ist, statt einen Kalender zu behaupten. Sommer
im April ist falsch, Lüften im April ist richtig.

Er bildet `heiz_kuhlfunktion` eins zu eins ab, ein Register, das der Controller
schreibt. Es gibt keine Übersetzungstabelle, die auseinanderlaufen kann.

Lüften ist ein sicherer Fallback. Weder heizen noch kühlen bedeutet, dass die
Grundfunktion weiterläuft. Bei Sensorausfall oder Widerspruch fällt der Controller
dorthin zurück, und das ist nie falsch, nur manchmal nicht optimal.

Keine Regel verzweigt je über den Modus selbst. Jede Regel liest ihr eigenes Gate
mit eigener Begründung, und der Modus ist nur eine Eingabe für dieses Gate. Eine
spätere Automatik der Umschaltung ist damit ein Wechsel der Quelle und keine
Änderung an der Logik. Dafür führt der Decision-Record schon jetzt die nötigen
Daten mit: gleitender Mehrtages-Mittelwert der Außentemperatur, Prognose und
Kühlpotenzial. Der Momentanwert allein taugt dafür nicht, `T10` stand Anfang
Oktober bei 20.9 Grad.

## Auflösung von Einstellungen

Jede Einstellung wird in der Reihenfolge Raum, Hub, Default aufgelöst, mit
absoluten Werten, nicht mit Offsets. Das gilt für Solltemperaturen, Zeiten,
Schwellwerte und Flags gleichermaßen. Ein Offset komponiert schlecht: ob er auch
auf den Urlaubswert und auf die Fenster-offen-Temperatur gehört, ist mal richtig
und mal Unsinn, und die Antwort müsste hart verdrahtet werden.

Jede Entscheidung nennt für jede benutzte Einstellung den Wert und die Quelle.
"Soll 18.5 Grad (Quelle Raum), Nachtbeginn 20:00 (Quelle Hub)" beantwortet die
Frage, ohne zwei Konfigurationsdialoge zu vergleichen.

Zusatzheizer nachts aus ist ein Raum-Feld in demselben Mechanismus und kein
Etagen-Konstrukt. Bei einem Haus, dessen Schlafräume zufällig das Obergeschoss
sind, ergibt das dasselbe Verhalten, bleibt aber richtig, wenn es einmal nicht so
ist.

## Räume

Ein Raum ist ein Name, eine Ist-Temperatur, null oder mehr Öffnungskontakte,
optional Feuchte und CO₂, und genau ein Aktor: eine `climate`-Entity.

Für die WGT-Räume ist das das Raumthermostat, dessen `hvac_mode` den Zusatzheizer
schaltet. Für Räume, die die WGT nicht heizt, ist es jede andere `climate`-Entity,
also ein Thermostatventil oder ein `generic_thermostat` vor einem Relais.

Der Controller regelt kein Relais selbst. Hysterese, Mindestlaufzeit und
Mindestpause macht `generic_thermostat` seit Jahren richtig, und selbstgeschriebene
sicherheitskritische Regelung ist genau die Klasse Code, die in v1 den Schaden
angerichtet hat. Der Preis ist ein Helper pro Relais-Raum, von Hand angelegt.

Null Öffnungskontakte ist ein gültiger Zustand. Nicht jeder Raum hat einen.

## Wärmepumpe

Die Freigabe folgt der Außentemperatur mit Hysterese um die Schwelle, und sie wird
nur geändert, wenn sie seit mindestens 30 Minuten stabil ist oder die Wärmepumpe
gerade nicht läuft. Beides ist aus `automation.heizung` übernommen, wo es sich
bewährt hat, und beides fehlte in v1.

Im Modus Kühlen gilt dieselbe Sperre für die Kühlfreigabe. Der billigste Weg
gewinnt: erst Nachtauskühlung über die Luftstufe, die Freigabe der Wärmepumpe erst,
wenn das nicht reicht.

Der Bypass ist Register 123 und nur lesbar. Der Controller kann ihn nie stellen,
also liest er ihn und erklärt ihn. Wenn bei Kühlbedarf der Bypass geschlossen
bleibt, ist das eine Meldung, keine Aktion.

## Luftstufe

Die Luftstufe ist zentral. Feuchte und CO₂ werden pro Raum gemessen, speisen aber
eine einzige Entscheidung, die sagt, welcher Raum welche Stufe fordert.

Luftqualität gewinnt, auch nachts. Achtundsiebzig Prozent im Bad über acht Stunden
sind ein Schimmelrisiko und teurer als eine Stufe Geräuschpegel. Wer das anders
will, schaltet den Lüfter-Modus auf `quiet`, dann gilt eine konfigurierbare
Obergrenze, und jede Entscheidung sagt, dass sie gedeckelt wurde. `boost` hebt
umgekehrt an. Beide bleiben stehen, bis sie umgeschaltet werden. Eine Ablaufzeit
kann später dazukommen.

Räume mit offenem Fenster fordern nichts. Ihre Feuchte- und CO₂-Werte messen
draußen.

## Sensorausfall

Ein Ausfall ist nie stumm und führt nie dazu, dass eine Regel klammheimlich
entfällt. v1 machte überall `if not state: continue`, womit ein toter CO₂-Sensor
gute Luft bedeutete und ein toter Fensterkontakt ein geschlossenes Fenster.

| Eingabe | Bei Ausfall |
| --- | --- |
| Öffnungskontakt | Gilt als offen. Lieber nicht heizen als gegen ein offenes Fenster heizen. |
| Außentemperatur | Letzter gültiger Wert bis zu einem Höchstalter, danach Rückfall auf Lüften. |
| Ist-Temperatur eines Raums | Der Raum behält seine Solltemperatur, der Zusatzheizer bleibt aus. |
| Feuchte, CO₂ | Die Regel entfällt für diesen Raum, sichtbar im Record. |
| Prognose, PV | Die Verfeinerung entfällt, die Basisregel bleibt. |

Dazu `binary_sensor` Eingeschränkt und ein Repair-Eintrag, wenn eine konfigurierte
Eingabe länger als eine Schwelle fehlt. Jeder Input steht mit Wert, Alter und
Gültigkeit im Decision-Record.

## Transparenz

Die Frage "warum ist der Zusatzheizer an" ist meistens eine Frage über die
Vergangenheit, und die Antwort muss einen Neustart und acht Stunden überleben.

Der aktuelle Zustand steht in den Attributen des Entscheidungs-Sensors: die Inputs
mit Alter und Gültigkeit, die Gates mit Ergebnis, die Einstellungen mit Quelle, und
ein fertiger Satz. Die umfangreichen Attribute werden vom Recorder ausgeschlossen,
weil sechs Räume alle 15 Minuten die Datenbank sonst zuschreiben.

Die Historie steht im Logbuch. Jede Änderung einer Entscheidung erzeugt einen
Eintrag mit dem fertigen Satz, pro Raum und für den Hub. Damit ist "warum war er um
drei Uhr an" ein Blick ins Logbuch des Raums.

Dazu kommen ein Diagnostics-Download für den vollen Schnappschuss und eine
Dashboard-Strategy mit Übersicht und Debug-View, wie in `cover-control`.

Benachrichtigungen gehen an einen `notify`-Service und werden fünf Minuten
gesammelt, damit eine Umschaltung, die sechs Räume betrifft, eine Nachricht ist
und nicht sechs. Wechsel der Wärmepumpenfreigabe wird gemeldet, so wie es
`automation.heizung` heute auch tut.

## Zusatzeingaben in v1

| Eingabe | Wirkung |
| --- | --- |
| Wetterprognose | Tageshöchstwert statt Momentanwert für die Heizfreigabe, Auslöser für Nachtauskühlung im Modus Kühlen, später Eingang für die Automatik der Modusumschaltung. |
| PV-Überschuss | Solltemperatur anheben oder Zusatzheizer freigeben, solange Überschuss anliegt. Die Begründung muss erklären, warum es 21.5 statt 20.0 Grad sind. |
| Türkontakte | Gehen in dieselbe Fenster-offen-Logik ein, mehrere Kontakte pro Raum. |

Urlaub bleibt ein manueller Schalter. Wer ihn automatisieren will, tut das in Home
Assistant, wie heute.

## Bewusst anders entschieden

Der Controller gewinnt immer. Es gibt keine Erkennung manueller Eingriffe und
keinen Übersteuerungs-Zustand, der hängenbleiben könnte. Am Raumthermostat zu
drehen hat damit keine bleibende Wirkung, und das ist der Preis dafür, dass der
Zustand des Controllers aus Konfiguration und Messwerten vollständig bestimmt ist.

Es gibt keine Boost-Buttons und keine Enable-Switches pro Raum. Nur die zentralen
Regler. Wer einen Raum dauerhaft anders will, ändert dessen Einstellung.

Modus und Urlaub sind zwei Achsen und keine flache Liste. Urlaub im Januar braucht
Frostschutz und abgesenkte Solltemperaturen, Urlaub im Juli nichts davon. Als
exklusiver vierter Modus müsste Urlaub die Jahreszeit trotzdem kennen, und diese
versteckte Verzweigung ist genau der Ort, an dem Begründungen verloren gehen.

Der Name trägt den Hersteller. Ein generischer Name wäre ein Versprechen, das der
Code nicht hält, und würde jede WGT-Eigenheit zu einem Sonderfall machen, den man
irgendwann abstrahieren müsste. So ist dieselbe Eigenheit das erklärte Thema.

Keine Zeitplan-Helper pro Raum. Nachtbeginn und Nachtende laufen durch denselben
Auflösungsmechanismus wie alles andere. Sechs Zeitpläne zu pflegen, deren
Begründung auf fremde Entities verweist, ist teurer als zwei Zahlen pro Raum.

## Nicht in v1

Automatik der Modusumschaltung. Die Datenquellen werden mitgeführt, die Umschaltung
bleibt manuell. Die Umschaltung ist teuer, also braucht sie Totband und eine
Verweildauer in Tagen, und das will beobachtet werden, bevor es automatisch läuft.

Anwesenheit und Kalender als Eingabe. Ein Handy im Flugmodus, das die Heizung
absenkt, während jemand daheim ist, ist ein schlechter Tausch für einen Schalter,
der funktioniert.

Fehler- und Filtermeldungen der Anlage, Strompreis und CO₂-Intensität des Netzes,
Adapter für Klimaanlagen.

## Offene Frage

Öffnet der Bypass auch bei Betriebsart `manual`, oder braucht er `Sommer`? Davon
hängt ab, ob Nachtauskühlung über die Luftstufe überhaupt wirkt. Solange das nicht
geklärt ist, ermittelt der Controller es selbst: er beobachtet `bypass_state`
gegen Außen- und Innentemperatur und meldet, wenn der Bypass bei Kühlbedarf
geschlossen bleibt.
