import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import scipy
import scipy.spatial

Wassernetz_koor = pd.read_csv('Wassernetz_Knoten.txt', delimiter = "\t")
Wassernetz_adja = pd.read_csv('WassernetzAdjazenz.txt', delimiter = "\t")
Wassernetz_Schleusen = pd.read_csv('SchleusenKnoten.txt', delimiter = "\t")

Schiene_koor = pd.read_csv('SchienennetzKnoten.txt', delimiter = "\t")
Schienen_adja = pd.read_csv('Schienennetz_Adjazenz.txt', delimiter = "\t")

WasserStraße_adja = pd.read_csv('StraßenWasserAdjazenz.txt', delimiter = "\t")
SchieneStraße_adja = pd.read_csv('SchieneStraßeAdjazenz.txt', delimiter = "\t")


points = pd.read_csv('StraßennetzKnoten.txt', delimiter = "\t")
edges = pd.read_csv('StraßeKanten.txt', delimiter = "\t")


G = nx.Graph()

#Wassernetz erstellen
for i in range(len(Wassernetz_koor)):
    G.add_node(i+30001, pos=(Wassernetz_koor["long"][i], Wassernetz_koor["lat"][i]))

for s in range(len(Wassernetz_Schleusen)):
    G.add_node(s+30201, pos=(Wassernetz_Schleusen["longS"][s], Wassernetz_Schleusen["latS"][s]))
    pointIDXYZ = nx.get_node_attributes(G, 'pos')

for e in range(len(Wassernetz_adja)):
    G.add_edge(Wassernetz_adja["from"][e], Wassernetz_adja["to"][e])


for t in range(len(Wassernetz_koor)):
    pointIDXYZ = nx.get_node_attributes(G, 'pos')

#Schienennetz erstellen
for p in range(len(Schiene_koor)):
 G.add_node(p+20001, pos=(Schiene_koor["long"][p], Schiene_koor["lat"][p]))

for t in range(len(Schiene_koor)):
 pointIDXYZ = nx.get_node_attributes(G, 'pos')

for e in range(len(Schienen_adja)):
 G.add_edge(Schienen_adja["from"][e], Schienen_adja["to"][e])

#Straßennetz erstellen
for t in range(11132):
    G.add_node(t,pos=(points['X'][t], points['Y'][t]))

for e in range(len(edges)):
    G.add_edge(edges['from'][e], edges['to'][e])

ponts = zip(points['X'], points['Y'])
pos = dict(zip(range(len(points)),ponts))

#Interlayer Verbindung Häfen und Schienennetz
for w in range(len(Wassernetz_koor)-5):
     G.add_edge(w+30001, w+20001)

#Doppelte Häfen entfernen
for u in range(len(Wassernetz_koor)+65):
    if u not in range(150,200):
        connected = False
        for v in range(len(Wassernetz_koor)+65):
            if v not in range(150, 200):
                if u != v:
                    if G.has_edge(u+30001, v+30001):
                        connected = True
        if not connected:
            G.remove_node(u+30001)


#Häfen ohne Schienennetzanschluss entfernen
for u in range(len(Schiene_koor)):
     connected = False
     for v in range(len(Schiene_koor)):
         if u != v:
             if G.has_edge(u+20001, v+20001):
                 connected = True
     if not connected:
         G.remove_node(u+20001)

#Interlayer Verbindung Häfen und Straßennetz
for m in range(len(WasserStraße_adja)):
   G.add_edge(WasserStraße_adja["from"][m],WasserStraße_adja["to"][m])

#Interlayer Verbindung Häfen und Schienennetz
for w in range(len(Wassernetz_koor)-5):
    G.add_edge(w+30001, w+20001, weight =100)



z = {**pos, **pointIDXYZ}

nx.draw(G, z, with_labels=True, font_weight='bold', node_size =0.1, font_size = 0.1, width = 0.2)
#nx.draw(G, pointIDXYZ, with_labels=True, font_weight='bold', node_size =0.1, font_size = 0.1, width = 0.2)
plt.savefig('NRWNetz.png', dpi =1000)
plt.show()

