# COT
## Rahmenbedingungen
- 2er Teams
- 15 Minuten Vortrag
- Termine im Januar (letzte Woche 2. Präsenzphase)
## Inhalt
- Stellen Sie einen selbst gewählten IoT/CoT-Anwendungsfall (z.B. Anbieter oder Forschungsprojekt) vor
### Geschäftsmodell (Business Model Canvas)
#### Kundensegmente: Für wen (Branchen, Privatpersonen etc.) kann die Lösung eingesetzt werden? (vgl. u.a. Roadmap Industrie 4.0)
#### Wertangebot: Welche Mehrwerte bietet die Lösung? Welche Komponenten umfasst diese technisch? (vgl. Value Proposition Canvas)
#### Wertschöpfungsarchitektur: Welche Komponenten werden von welchen Akteuren bereit gestellt? (vgl. 5 Ebenen Modell der IoT nach Fleisch et al.)
#### Ertragsmodell: Wie verdient der Anbieter damit Geld (bzw. plant Geld zu verdienen)? (vgl. Ertragsmodellmuster nach Wortmann et al.)
- Free for academic use (Forschungsinstitutionen müssen nur die Geräte erwerben zum Einkaufspreis, es muss keine monatliche Zahlung für die Service-Erbringung gezahlt werden)
- Für alle anderen setzen sich die Kosten aus einmaligen Kosten für Geräte und Installation und laufenden Kosten in Form einer Service Pauschale für Betrieb und Wartung für die Messaging und Cloud-Plattform zusammen
### Technische Architektur
- Beschreiben Sie aufbauend auf den Erfahrungen der genutzten Demo Boards die technische Architektur der Lösung an einzelnen Beispielen
## Ideen
- Corona Luftfeuchtigkeitstracker mit Ampelsystem und Dashboard für Pandemie-Verantwortlichen
- https://healthcare-in-europe.com/de/news/welche-rolle-spielt-luftfeuchtigkeit-bei-der-verbreitung-von-sars-cov-2.html
- Grundsätzlich: Liegt die relative Luftfeuchtigkeit der Raumluft unter 40 Prozent, dann nehmen die von Infizierten ausgestoßenen Partikel weniger Wasser auf, bleiben leichter, fliegen weiter durch den Raum und werden eher von Gesunden eingeatmet. Durch eine geringere Luftfeuchtigkeit sind auch die Schleimhäute empfänglicher für Aufnahme von Virus-Aerosolen. Durch Lüftung kann die Raum-Luftfeuchtigkeit durch die durchschnittliche Außen-Luftfeuchtigkeit von 70-90% in Deutschland erhöht werden.
-Luftfeuchtigkeit soll per MQTT zentral gemeldet werden, dort werden die Werte mit Außen-Luftfeuchtigkeiten abgeglichen
-wenn die Luftfeuchtigkeit außen hoch genug ist und die Raum-Luftfeuchtigkeit zu niedrig, wird eine Lüftung vorgeschlagen und aktuelle Werte auf dem Display ausgegeben
-wenn die Raum-Luftfeuchtigkeit zu niedrig ist, und die Außen-Lufttemperatur nicht ausreicht, wird die Lüftung mit einem Lüftfeuchter angestoßen und aktuelle Werte auf dem Display ausgegeben
-alle Räume und deren Zustand wird in einem Dashboard für den Pandemie-Verantwortlichen sichtbar gemacht
## Verkabelung
- Temperatur/Luftfeuchtigkeitssensor (I2C, DATA GPIO21, CLK GPIO23)
- LCD Panel (Speaker)
- 2 Relais (GPIO13, GPIO12)


