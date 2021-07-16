Diese README-Datei soll einen kurzen Einblick in unseren Code liefern. Für eine detaillierte Beschreibung wird auf den im Rahmen des Teamprojekts enstandenen Bericht verwiesen.

AUTOREN: 
Sven Daschek, Jakob Freytag und Linus Schulze

GENERAL:
Die GIS-Daten der Modellregion NRW werden in diesen Dateien in ein Networkx-Netzwerk umgewandelt. Die Standorte der Knotenpunkte werden aus 
Koordinaten in CSV-Dateien eingelesen und die Kanten über Adjazenzmatrizen erstellt. Der Übersicht halber sind die Knoten- und Adjazenz-Informationen jeweils in einer eigenen Datei für jede Layer und zusätzlich nochmal die Interlayer Verbindungen. Dies dient einer einfacheren Differenzierung der jeweiligen Layer bei einer Implementierung in den Hauptcode. Die Knoten sind aber auch anhand ihrer ID einer Layer zuordbar. Die IDs der Straßennetzknoten fangen bei 1 an, die Schienenetzknoten bei 20000, Häfen ab 30000 und Schleusen ab 30200.

EINORDNUNG DER KNOTEN ZU IHREN LAYERN:
Der Übersicht halber sind die Knoten- und Adjazenz-Informationen jeweils in einer eigenen Datei für jede Layer und zusätzlich nochmal die Interlayer Verbindungen. Dies dient einer einfacheren Differenzierung der jeweiligen Layer bei einer Implementierung in den Hauptcode. Die Knoten sind aber auch anhand ihrer ID einer Layer zuordbar. Die IDs der Straßennetzknoten fangen bei 1 an, die Schienenetzknoten bei 20000, Häfen ab 30000 und Schleusen ab 30200. Da ein Großteil der Häfen auch als Bahnhofsknoten im Schienennetz existiert, sind diese Interlayer Verbindungen in der Wassernetz-Adjazenzmatrix enthalten. 

NETZWERKAUFBAU:
Es werden zunächst alle Knoten des Wassernetzes eingelesen, einige Knoten im Datensatz beschreiben jedoch den gleichen Hafen, was vor allem bei größeren Häfen mit mehreren Becken auftritt. Von mehreren Knoten für einen Hafen ist jedoch nur einer in der Ajazenzmatrix enthalten und dementsprechend werden Knoten ohne eine Kante zu anderen Knoten wieder entfernt. Ähnlich ist dies beim Schienennetz. Da viele Häfen einen Anschluss an das Schienennetz besitzen, werden diese auch als Knoten dieser Ebene eingelesen. Hier tauchen jedoch auch wieder nur die Häfen in der Adjazenz auf, welche auch einen Anschluss an das Schienennetz haben, die Restlichen werden entfernt. Häfen mit einem Schienennetzanschluss existieren also jeweils einmal als Hafen im Wassernetz und einmal als Bahnhof im Schienennetz.

Einordnung zu Realdaten:
Oft ist in den CSV-Dateien eine dritte Spalte enthalten welche den jeweiligen Fluss oder Kanal für die Verbindungen markiert, aufgrund des Datenmangels sind aber nicht alle Häfen direkt benannt. Die Schleusen sind jedoch alle benannt und in der CSV-Datei sind auch schon die jeweiligen Verfübarkeiten der Schleusen enthalten. Zu bemerken ist, dass sich in den Schleusen der Knoten "209" eingeschlichen hat, welcher doch keine Schleuse ist. Er kommt im Netzwerk nicht vor, ist jedoch noch in der Excel enthalten, da eine Entfernung der Zeile die IDs für die Adjazenzmatrizen verschieben würde. 

