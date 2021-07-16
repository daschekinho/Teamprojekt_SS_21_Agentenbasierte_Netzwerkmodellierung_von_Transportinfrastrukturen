import networkx as nx
import numpy as np
import random as rm
import matplotlib.pyplot as plt
import time
from layer import Layer
from MultiLayerGraph import MultiLayerGraph
from agent import agent
from collections import Counter
import pandas as pd

time_start = time.time()
time_start_proc = time.process_time()

# Default-Einstellungen des Netzwerks, die über folgende Flags gesteuert werden
n_timesteps = 15+1 # Anzahl an Perioden
n_networks = 1 # Anzahl an Netzwerken, die gebildet werden sollen; es wird empfohlen immer eins aufzubauen
dv = 0.05 # distrubtion_value; Wahrscheinlichkeit, mit der ein Knoten disrupted wird, falls dv=0 gibt es keine Disruptions
dt = 3 # disruption_time; bestimmt wie lange die Disruptions andauern
dp = 3 # disruption_period; bestimmt dass nur jede dp-te Periode es zu Disruptions kommen kann
lyr_similar_load = False # falls True, wird zu Beginn durch die Anzahl an generierten Agenten der Layer ein Loadausgleich unter den Layern durchgeführt
ag_gen_laufzeit = True # falls True werden Agenten zur Laufzeit bei der Periode generiert und es findet automatisch eine Layerloadanpassung nach lyr_similar_load pro Periode statt
gen_at_dis_node = True # falls True, können neue Agentena an disrupted Knoten generiert werden
bool_perf_ag = False # falls True, sind die Agenten perfekte Agenten
dc_verändern = True # falls True, haben bei einer Disruption die Knoten keinen Totalausfalls, sondern verringern ihre Servicerate und Bufferkapazität
dc_aufhebung = False # falls True, wird eine Dirsruption nach dc_verändern schrittweise aufgehoben
dc_buffer = 0.3 # bestimmt zu wie viel Prozent die Bufferkapazität nach dc_verändern eingeschränkt werden sollen
dc_service_rate = 0.3 # bestimmt zu wie viel Prozent die Servierate nach dc_verändern eingeschränkt werden sollen
default_network = 'ja' # falls ungleich 'nein', so kommt es zu keiner Userabfrage über die Konsole und das Netzwerk wird nach den Defaultwerten aufgebaut

# Layer-Eigenschaften definieren:
# id, name, number_of_nodes, service_rate, buffer, connectivity, Transportzeit, load, probability_gen_agent, hubs, colour in layerplot, max_queue_cost)
ly1 = Layer(id=1, name='water', nn=15, sr=640, bu=400, connect=0.01, ed_time=5, ld=200, p_gen_agent=0.5, hubs=3, colour='lightblue', max_queue_cost=5)
ly2 = Layer(id=2, name='train', nn=30, sr=640, bu=500, connect=0.05, ed_time=1, ld=200, p_gen_agent=0.5, hubs=6, colour='r', max_queue_cost=1)
ly3 = Layer(id=3, name='street', nn=150, sr=640, bu=1000, connect=0.01, ed_time=2, ld=10, p_gen_agent=0.5, hubs=10, colour='yellow', max_queue_cost=2)
# Beispiel für weitere Layer:
# ly4 = Layer(id=4, name='air', nn=10, sr=640, bu=800, connect=0.3, ed_time=2, ld=100, p_gen_agent=0.5, hubs=4, colour='green', max_queue_cost=7)
# ly5 = Layer(id=5, name='pipeline', nn=30, sr=640, bu=300, connect=0.3, ed_time=4, ld=5, p_gen_agent=0.5, hubs=3, colour='pink', max_queue_cost=2)

# Dient der Übersicht über die erzeugten Layer
temp_list = []
for i in Layer.list_of_layers:
    temp_list.append([i.name, i.number_of_nodes])
print(f'list_of_layers: {temp_list}')

# Nachfolgend findet die Benutzerabfrage über die Konsole statt.
# Das Netzwerk kann jedoch schneller gestaltet werden, indem man die Layer-Eigenschaften im Code festlegt
# Ansonsten wird man selbsterklärend durch die Erstellung geleitet und ggf. wird bei einer flaschen Eingabe ein Fehler geworfen

#default_network = input("Möchten Sie das Netzwerk mit den Standard-Attributen aufbauen? (Ja oder Nein) ")
if default_network.lower().strip() == 'nein':
    n_networks = int(input("Wie viele Netzwerke möchten Sie erstellen? (Default: 1) "))
    n_timesteps = int(input("Wie viele Timesteps möchten Sie haben? (Default: 15) ")) +1
    bool_perf_ag = input('Soll es perfekte Agenten geben? (Default: Nein')
    if bool_perf_ag.strip().lower() == 'ja':
        bool_perf_ag = True
    dv = float(input("Wie stark sollen die Netzwerke disrupted werden? (zwischen 0 und 1) (default=0) "))
    if dv < 0 or dv > 1:
        raise ValueError("Disruption Value muss zwischen 0 und 1 sein.")
    if dv > 0:
        dt = int(input("Wie lange sollen die Knoten disrupted sein? (default = 5) "))
        dp = int(input("Wie oft soll es die Möglichkeit geben, dass die Knoten disrupten? Jeden i-ten Timestep (default= 3)"))
        dc = input("Soll die Disruption einen Ausfall der Knoten zur Folge haben oder die Eigenschaften der Knoten Verändern? (Aus oder Eig) (default=Aus) ")
        if dc.lower().strip() == 'eig':
            dc_verändern = True
            dc_buffer = float(input("Wie stark soll der Puffer durch eine Disruption eingeschränkt werden. (in %(0.X))"))
            if dc_buffer < 0 or dc_buffer > 1:
                raise ValueError("dc_buffer muss zwischen 0 und 1 liegen.")
            dc_service_rate = float(input("Wie stark soll die Service Rate durch eine Disruption eingeschränkt werden. (in %(0.X))"))
            if dc_service_rate < 0 or dc_service_rate > 1:
                raise ValueError("dc_servie_rate muss zwischen 0 und 1 liegen.")
            if dt>1:
                dc_auf = input("Sollen die Disruptions langsam wieder aufgehoben werden? Ja oder Nein")
                if dc_auf.lower().strip() == 'ja':
                    dc_aufhebung = True
    temp_ag_gen_laufzeit = input("Sollen Agenten zur Laufzeit generiert werden und eine Loadanpassung stattfinden? (Default: Nein) ")
    if temp_ag_gen_laufzeit.lower().strip() == 'ja':
        ag_gen_laufzeit = True
        if dv > 0:
            gen_at_dis_node_answer = input("Dürfen Agenten an disrupted Knoten generiert werden? (Default: Ja) ")
            if gen_at_dis_node_answer.lower().strip() == 'nein':
                gen_at_dis_node = False
    else:
        temp_lyr_similar_load = input("Sollen die Layer-Loads in t=1 angeglichen werden? (Default: Nein) ")
        if temp_lyr_similar_load.lower().strip() == 'ja':
            lyr_similar_load = True

    # ab hier beginnt die Festlegung der Layereigenschaften
    abfrage_layer_details = input("Möchten Sie die Standard Layer Eigenschaften nutzen? (Ja oder Nein) ")
    if abfrage_layer_details.lower().strip() == 'nein':
        n_layer = int(input("Aus wie vielen Layern sollen die Netzwerke bestehen? (Default: 3) "))
        Layer.list_of_layers.clear()
        for i in range(0, n_layer):
            numb_nodes = int(input(f'Anzahl an Knoten des {i+1}. Layers:'))
            ly_id = i + 1
            ly_name = input(f'Name des {i+1}. Layer:')
            ly_service_rate = int(input(f'Service-Rate des {i+1}. Layers:'))
            ly_buffer = int(input(f'Buffer der Knoten des {i+1}. Layers:'))
            ly_load = int(input(f'Load im {i + 1}. Layer:'))
            ly_connectivity = float(input(f'Konnektivität des {i+1}. Layers (0-1) (Bitte orientieren Sie sich an den Defaultwerten):'))
            if ly_connectivity < 0 or ly_connectivity > 1:
                raise ValueError("ly_connectivity muss zwischen 0 und 1 liegen.")
            ly_hubs = int(input(f'Anzahl an Hubs in {i + 1}. Layer:'))
            if ly_hubs > numb_nodes:
                raise ValueError('Es kann nicht mehr Hubs als Knoten in einem Layer geben')
            ly_edge_time = int(input(f'Kantendauer im {i+1}. Layer:'))
            ly_max_queue_cost = int(input(f'Max. Kosten bei voller Queue des {i + 1}. Layers: '))
            ly_prob_gen_agent = float(input(f'Wahrscheinlichkeit der Agentengenerierung des {i+1}. Layers: '))
            if ly_prob_gen_agent < 0 or ly_prob_gen_agent > 1:
                raise ValueError("ly_prob_gen_agent muss zwischen 0 und 1 liegen.")
            if i != n_layer-1:
                print('=== nächster Layer ===')
            Layer(ly_id, ly_name, numb_nodes, ly_service_rate, ly_buffer, ly_connectivity, ly_edge_time, ly_load, ly_prob_gen_agent, ly_hubs, ly_max_queue_cost)

print("Timesteps: " + str(n_timesteps))
print("Anzahl Netzwerke: " + str(n_networks))


# Hilfslisten zum Plotten der Agentencounts
agents_per_timestep = []
generated_agents_per_timestep = []
delivered_agents_per_timestep = []
f_disrupt_agents_per_timestep = []
f_no_next_agents_per_timestep = []
f_pfad_agents_per_timestep = []
f_queue_agents_per_timestep = []
f_gen_agents_per_timestep = []
f_gen_full_buffer_per_timestep = []
f_cost_per_timestep = []
nodes_where_agents_failed = []
node_traffic = []
load_per_node = []

# dc_qutioent bestimmt bei perf_Agenten=True und dc_verändern=True zu welcher Wahrscheinlichkeit ein Knoten von perf. Agenten gemieden werden soll
# setzt sich aus dem Mittelwert der Einschrämkungen für die Buffer und Servieraten zusammen
if dc_buffer==1 or dc_service_rate==1:
    dc_quotient = 1
else:
    dc_quotient = (dc_buffer + dc_service_rate)/2

# h_init_gen_p bestimmen (Annahme: Es soll ungefähr gleich viel Load auf den Layern erzeugt werden)
# Zielload ist dabei der maximale Load unter den Layern ohne Anpassung
# dieser Wert wird dem jeweiligen Layer über die Klassenliste hinzugefügt
anfangs_load = []
max_load = 0
for i in Layer.list_of_layers:
    x = i.number_of_nodes * i.probability_gen_agent * i.load
    anfangs_load.append(x)
max_load = max(anfangs_load)
for i in Layer.list_of_layers:
    i.h_init_gen_p = round(max_load / (i.number_of_nodes * i.probability_gen_agent * i.load))
    print(i.h_init_gen_p)

# Diese Methode ist für die ganzen Plots verantwortlich
def plot_all(mg):

    # Agenten Kosten Vergleich
    nodes_where_agents_failed.append(mg.nodes_waf)
    node_traffic.append(mg.node_traffic)
    data = mg.route_cost_comp

    # Netzwerkplot (gesamt; wird nicht geplottet, falls in MultiLayerGraph auskommentiert)
    plt.legend()
    plt.show()

    # Layerplot
    for i in Layer.list_of_layers:
        plt.figure(i.id)
        ax = plt.gca()
        ax.set_title(i.name)
        nx.draw(i.network, node_color=i.colour,
                with_labels=True,
                node_size=500)
    plt.show()

    # Listen mit Nullen auffüllen um gleiche Länge zu garantieren, da diese nur während der Generierung zur Laufzeit gefüllt sind
    while len(generated_agents_per_timestep) != n_timesteps:
        generated_agents_per_timestep.append(0)
    while len(f_gen_agents_per_timestep) != n_timesteps:
        f_gen_agents_per_timestep.append(0)
    while len(f_gen_full_buffer_per_timestep) != n_timesteps:
        f_gen_full_buffer_per_timestep.append(0)
    while len(f_cost_per_timestep) != n_timesteps:
        f_cost_per_timestep.append(0)

    # Agentenübersichtsplot
    t = list(range(0, n_timesteps))
    plt.xlabel('timesteps')
    plt.ylabel('number of agents')
    plt.title('State of Agents in Network ' + str(mg.ID))
    plt.plot(t, agents_per_timestep, marker='.', label='Number of Agents in Network')
    plt.plot(t, delivered_agents_per_timestep, marker='.', label='Number of Delivered Agents')
    plt.plot(t, f_disrupt_agents_per_timestep, marker='.', label='Number of Disrupted Agents')
    plt.plot(t, f_no_next_agents_per_timestep, marker='.', label='Number of Failed Agents: No Next')
    plt.plot(t, f_queue_agents_per_timestep, marker='.', label='Number of Failed Agents: Queue')
    plt.plot(t, f_pfad_agents_per_timestep, marker='.', label='Number of Failed Agents: Pfad')
    plt.plot(t, f_gen_agents_per_timestep, marker='.', label='Number of Failed Agents: Gen')
    plt.plot(t, f_gen_full_buffer_per_timestep, marker='.', label='Number of Failed Agents: Gen Full Buffer')
    plt.plot(t, f_cost_per_timestep, marker='.', label='Number of Failed Agents: Cost (p_ag)')
    plt.xticks(list(range(0, n_timesteps)))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=2)
    plt.tight_layout()
    plt.show()

    # andere Hilfslisten, die für den Stackplot benötigt werden
    diff_generated = np.diff(generated_agents_per_timestep)
    generated_plot = diff_generated.tolist()
    generated_plot.insert(0, generated_agents_per_timestep[0])
    #Hilfsliste temp... um im Plot nicht den Eindruck zu erwecken, dass es doppelt so viele Agenten in t=1 gibt
    temp_agents_p_ts = agents_per_timestep
    temp_agents_p_ts[0]= 0

    # Unterscheidung beim Stackplot, ob Agentengenerierung zur Laufzeit an ist oder nicht
    if ag_gen_laufzeit == True:
        agent_plot_values = {
            'generated': generated_plot,
            'On Tour': temp_agents_p_ts,
            'arrived': delivered_agents_per_timestep,  # hier arrived_count--> das aus agents_delivered_count
            'FAILED: Disrupt': f_disrupt_agents_per_timestep,
            'FAILED: No next': f_no_next_agents_per_timestep,
            'FAILED: Pfad': f_pfad_agents_per_timestep,
            'FAILED: Queue': f_queue_agents_per_timestep,  # arrays durch
            'FAILED: Gen' : f_gen_agents_per_timestep,
            'FAILED: Gen Full Buffer' : f_gen_full_buffer_per_timestep,
            'FAILED: Cost (p_Ag)' : f_cost_per_timestep,
        }
    else:
        agent_plot_values = {
            'generated': generated_agents_per_timestep,# [] hier generated_count
            'On Tour': temp_agents_p_ts,
            'arrived': delivered_agents_per_timestep,  # hier arrived_count--> das aus agents_delivered_count
            'FAILED: Disrupt': f_disrupt_agents_per_timestep,
            'FAILED: No next': f_no_next_agents_per_timestep,
            'FAILED: Pfad': f_pfad_agents_per_timestep,
            'FAILED: Queue': f_queue_agents_per_timestep,  # arrays durch
            'FAILED: Gen': f_gen_agents_per_timestep,
            'FAILED: Gen Full Buffer': f_gen_full_buffer_per_timestep,
            'FAILED: Cost (p_Ag': f_cost_per_timestep,
        }

    fig, ax = plt.subplots()
    ax.stackplot(t, agent_plot_values.values(), labels=agent_plot_values.keys())
    plt.xticks(t)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=3)
    ax.set_title('Agentstatus in Network per Timestep')
    ax.set_xlabel('Timesteps')
    ax.set_ylabel('Agentenanzahl nominal')
    plt.tight_layout()
    plt.show()

    # Plot vom Pie-Chart für Failed-Agents per Layer
    failed_agents_per_lyr = []
    labels = []
    fig1, ax1 = plt.subplots()
    plt.title('Failed Agents per Layer')
    for i in Layer.list_of_layers:
        failed_agents_per_lyr.append(mg.lyr_id_fail.count(i.id))
    total = sum(failed_agents_per_lyr)
    for i in Layer.list_of_layers:
        labels.append([i.name, ("#Knoten:", i.number_of_nodes), ("Ag failed: Absolut:",(mg.lyr_id_fail.count(i.id))),
                       ("In Prozent: " + "{:.2%}".format((mg.lyr_id_fail.count(i.id)/total)))])
    # Beschriftungen auf dem Pie-Chart
    ax1.pie(failed_agents_per_lyr, labels=None, autopct=None, shadow=True, startangle=180)
    ax1.axis('equal')
    ax1.legend(labels= labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=1)
    plt.tight_layout()
    plt.show()

    # Plot für Zentralitätseigenschaft
    nodes_where_agents_failed.append(mg.nodes_waf)  # Listen beschaffen
    node_traffic.append(mg.node_traffic)
    load_per_node.append(mg.load_per_node)

    nodes_where_agents_failed_un = [item for sublist in nodes_where_agents_failed for item in
                                    sublist]  # Listen in Listen "entpacken"
    node_traffic_un = [item for sublist in node_traffic for item in sublist]
    load_per_node_un = [item for sublist in load_per_node for item in sublist]

    nodes_waf_quantity = dict(Counter(nodes_where_agents_failed_un))  # Knoten in Listen zählen
    node_traffic_quantity = dict(Counter(node_traffic_un))
    load_per_node_quantity = dict(Counter(load_per_node_un))

    for i in range(len(load_per_node_un)):  # Knoten ohne Agents Failed oder Traffic mit Wert 0 in dict aufnehmen
        if i not in nodes_waf_quantity:
            nodes_waf_quantity[i] = 0
        if i not in node_traffic_quantity:
            node_traffic_quantity[i] = 0

    nodes_waf_quantity_sorted = sorted(nodes_waf_quantity, key=(lambda key: nodes_waf_quantity[key]), reverse=True)
    node_traffic_quantity_sorted = sorted(node_traffic_quantity, key=(lambda key: node_traffic_quantity[key]),
                                          reverse=True)

    # 5 Knoten mit meisten Agents Failed
    print("Nodes with highest number of agents failed (" + str(
        len(nodes_where_agents_failed_un)) + " agents failed in total):")
    for i in range(5):
        print("Node (Layer):", nodes_waf_quantity_sorted[i],
              "(" + str(nx.get_node_attributes(mg, 'Layer')[nodes_waf_quantity_sorted[i]]) + ")",
              "Number of agents failed:", nodes_waf_quantity[nodes_waf_quantity_sorted[i]])

    print("")

    # 5 Knoten mit höchstem Verkehrsaufkommen
    print("Nodes with highest traffic (" + str(len(node_traffic_un)) + " node surpasses in total):")
    for i in range(5):
        print("Node (Layer):", node_traffic_quantity_sorted[i],
              "(" + str(nx.get_node_attributes(mg, 'Layer')[node_traffic_quantity_sorted[i]]) + ")",
              "Number of agent surpasses:", node_traffic_quantity[node_traffic_quantity_sorted[i]])

    # Plot für 5 Knoten mit höchstem Verkehrsaufkommen
    top5ID = []
    top5AF = []
    top5Traffic = []
    top5Load = []
    top5degree = []
    for i in range(5):
        top5ID.append(node_traffic_quantity_sorted[i])
        top5Traffic.append(node_traffic_quantity[node_traffic_quantity_sorted[i]])
        top5AF.append(nodes_waf_quantity[node_traffic_quantity_sorted[i]])
        top5Load.append(load_per_node_un[node_traffic_quantity_sorted[i]])
        top5degree.append(mg.degree[node_traffic_quantity_sorted[i]])
    top5 = zip(top5ID, top5Traffic, top5AF, top5Load, top5degree)

    traffic_mean = round(np.mean(list(node_traffic_quantity.values())), 2)
    AgentsFailed_mean = round(np.mean(list(nodes_waf_quantity.values())), 2)
    traffic_standardeviation = round(np.std(list(node_traffic_quantity.values())), 2)
    AgentsFailed_standardeviation = round(np.std(list(nodes_waf_quantity.values())), 2)
    LoadPerNode_mean = round(np.mean(list(load_per_node_quantity.values())), 2)
    LoadPerNode_standarddeviation = round(np.std(list(load_per_node_quantity.values())), 2)

    top5df = pd.DataFrame(top5)
    top5df.columns = ['ID', 'Traffic', 'Agents Failed', 'Load', 'degree']

    top5df['Node-ID (Node-Degree)'] = top5df['ID'].astype(str) + " (" + top5df['degree'].astype(str) + ")"
    del top5df['degree']
    del top5df['ID']

    top5df.plot.bar(title="Top 5 nodes with highest volume of traffic", x='Node-ID (Node-Degree)',
                    secondary_y='Load', legend=False)
    top5colors = {'Traffic': 'blue', 'Agents failed': 'darkorange', 'Load': 'green'}
    top5labels = ['Traffic', 'Agents failed', 'Load']
    top5handles = [plt.Rectangle((0, 0), 1, 1, color=top5colors[label]) for label in top5labels]
    top5labels[0] = top5labels[0] + ' (µ = ' + str(traffic_mean) + ' , σ = ' + str(traffic_standardeviation) + ')'
    top5labels[1] = top5labels[1] + ' (µ = ' + str(AgentsFailed_mean) + ' , σ = ' + str(
        AgentsFailed_standardeviation) + ')'
    top5labels[2] = top5labels[2] + ' (Right Y-Axis) (µ = ' + str(LoadPerNode_mean) + ' , σ = ' + str(
        LoadPerNode_standarddeviation) + ')'
    plt.legend(top5handles, top5labels, bbox_to_anchor=(0.65, -0.4), fontsize=10)
    plt.xticks(rotation=45)
    # plt.gcf().text(0.5, 0.175, "Hallo Test", fontsize=14)
    plt.tight_layout()
    plt.show()

    #Hilfslisten leeren damit nächstes Netzwerk diese Nutzen kann
    agents_per_timestep.clear()
    generated_agents_per_timestep.clear()
    delivered_agents_per_timestep.clear()
    f_disrupt_agents_per_timestep.clear()
    f_no_next_agents_per_timestep.clear()
    f_pfad_agents_per_timestep.clear()
    f_queue_agents_per_timestep.clear()
    f_gen_agents_per_timestep.clear()
    f_gen_full_buffer_per_timestep.clear()
    top5ID.clear()
    top5AF.clear()
    top5Traffic.clear()
    top5Load.clear()
    top5degree.clear()
    nodes_where_agents_failed.clear()
    node_traffic.clear()
    load_per_node.clear()


# Ab hier beginnt die Abarbeitung der erstellten Netwzerke
for i in range(0, n_networks + 1):  # +1, weil erstes Netzwerk nur zur Initialiserung dient

    # Eigentliche Net6werkerzeugung
    mg = MultiLayerGraph(i, Layer.list_of_layers)
    # erstes 'Netzwerk' dient nur der Überschriften-Initialisierung
    if i == 0:
        continue

    time_temp = time.time()
    zwischenzeit = time_temp - time_start
    print('T0:', '{:5.3f}s'.format(zwischenzeit))
    print("")

    # Übersicht über die sortierten Knotengrade in einem Layer
    # so kann überprüft werden, ob das erzeugte Netzwerk ggf. zu dicht/die Konnektivität zu hoch ist
    # kann in den Layereigenschaften, bzw. indem set_inter_layer_edges angepasst wird, reguliert werden
    degree_list = list(mg.degree)
    degree_list.sort(key=lambda x: x[1], reverse=True)
    print(f'==> nach dem Verbinden: Degree der Knoten im gesamten Netzwerk: {degree_list}')
    # for i in Layer.list_of_layers:
    #     layer_degree_list = list(i.network.degree)
    #     layer_degree_list.sort(key=lambda x: x[1], reverse=True)
    #     print(f'Layer {i.name} hat folgende Degrees: {layer_degree_list}')
    # print("")

    # Agentengenerierung und Layer Load-Anpassung
    if lyr_similar_load == True:
        # Mehrere initiale Durchläufe, sodass Load pro Layer ungefähr gleich ist, indem mehr Agenten erzeugt werden
        for i in Layer.list_of_layers:  # für jeden Layer
            for j in range(0, i.h_init_gen_p):  # h_init_gen_p oft durchlaufen
                for k in i.node_list:
                    agent_id = mg.agent_count
                    p_generate = rm.random()
                    if p_generate <= i.probability_gen_agent:
                        start = nx.get_node_attributes(mg, 'ID')[k]
                        load = mg.node_load[start]
                        ag_NEW = agent(mg, agent_id, load, start)

    # Normale Agentengenerierung ohne Load-Anpasssung
    else:
        for j in range(len(mg.nodes)):
            agent_id = mg.agent_count
            temp_prob = nx.get_node_attributes(mg, 'Prob_Gen_Agent')[j]
            p_generate = rm.random()
            if p_generate <= temp_prob:
                start = nx.get_node_attributes(mg, 'ID')[j]
                load = mg.node_load[start]
                ag_NEW = agent(mg, agent_id, load, start)


    # das erste Aufrufen von update_edges() nach initialer Agentengenerierung, da Knoten mit neuen Agenten befüllt sind
    # und so sich die Kantenkosten schon verändern; es können sogar schon erste Agenten failen
    mg.update_edges(mg.agent_list)
    generated_agents_per_timestep.append(mg.agents_generated_count)

    # Routengenerierung für initial erzeugte Agenten
    for ag in (mg.agent_list):
        ag.get_route()
        ag.display_agent()

    # Beginnd er großen for-Schleife füe jeden Timestep
    for t in range(1, n_timesteps + 1):
        print()
        print('===================================')
        print('TIMESTEP:', t)
        print('===================================')
        print()

        # Abfrage ob Knoten disruptet werden sollen; soll nicht in erster Periode geschehen
        if t > 1 and dv > 0:
            if t%dp == 0:
                mg.disrupt_network(t, dv, dt, dc_verändern, dc_buffer, dc_service_rate)
            mg.restore_disruption(t, dc_verändern, dc_aufhebung, dc_buffer, dc_service_rate)

        #Agenten Generierung zur Laufzeit
        if ag_gen_laufzeit == True:
            if t > 1: # nicht für erste Periode, wegen initialer Generierung
                for i in Layer.list_of_layers:
                    for j in range(0, i.h_init_gen_p):
                        for k in i.node_list:

                            if gen_at_dis_node == True: # Agentengenerierung an disrupted Knoten erlaubt
                                agent_id = mg.agent_count
                                p_generate = rm.random()
                                if p_generate <= i.probability_gen_agent:
                                    start = nx.get_node_attributes(mg, 'ID')[k]
                                    load = mg.node_load[start]
                                    ag_NEW = agent(mg, agent_id, load, start)
                                    if mg.node_disrupted[k]:
                                        ag_NEW.fail('GEN AT DISRUPTED NODE') # Agentengenerierung an disrupted Knoten erlaubt, aber failen, weil disrupted
                                    else:
                                        ag_NEW.get_route()
                                        ag_NEW.display_agent()

                            else: # Agentengenerierung an disrupted Knoten verboten, können so auch nicht dort direkt failen
                                agent_id = mg.agent_count
                                p_generate = rm.random()
                                if p_generate <= i.probability_gen_agent and mg.node_disrupted[k] == False:
                                    start = nx.get_node_attributes(mg, 'ID')[k]
                                    load = mg.node_load[start]
                                    ag_NEW = agent(mg, agent_id, load, start)
                                    ag_NEW.get_route()
                                    ag_NEW.display_agent()

                generated_agents_per_timestep.append(mg.agents_generated_count)
                f_gen_agents_per_timestep.append(mg.count_failed_gen)

        # die Knoten beginnen neue Perioden immer mit voller Service-Rate
        service_rate = nx.get_node_attributes(mg, 'Service Rate')
        # Aufruf von update_edges, das sich durch Agentengernerierung zur Laufzeit, die Kantenkosten verändert haben
        # wichtig für den perfekten Agenten
        if t > 1:
            mg.update_edges(mg.agent_list, bool_perf_ag=bool_perf_ag, dc_verändern=dc_verändern, dc_quotient=dc_quotient)

        # folgende Aktionen werden für jeden Agenten im Netzwerk durchgeführt
        for ag in list(mg.agent_list):
            ag.t += 1 # Zeit, die Agent im NEtzwerk ist hochsetzen
            standort = ag.so
            ladung = ag.load

            # Unterscheidung ob Agent sich auf Kante oder Knoten befindet; hier Knoten:
            if ag.at_edge == False:
                # Perfekter Agent an, also Routengenerierung an jeden Knoten
                if bool_perf_ag == True and ag.t > 1 and ag.route['path'] != False:
                    alte_route = ag.route['path'] # alte Route ab neuem Knoten! (del path[0] davor in go_next)
                    alte_route_alte_kosten = ag.route['cost']
                    alte_route_neue_kosten = 0

                    for i in alte_route:
                        index = alte_route.index(i)
                        if index+1 < len(alte_route):
                            alte_route_neue_kosten += mg.edge_total_cost[(i, alte_route[index+1], 0)]

                    ag.get_route() # neue Route
                    neue_route = ag.route['path']
                    neue_route_kosten = ag.route['cost']

                    # Anzahl Route Changes, falls neue Route anders ist
                    if alte_route != False:
                        veränderung = all(node in alte_route for node in neue_route) # Test ob neue Route andere Knoten beinhaltet
                        if veränderung == False :
                            print(f'Agent {ag.ID} hat von {alte_route} (Kosten: {alte_route_neue_kosten}) zu '
                                  f'{neue_route} (Kosten: {neue_route_kosten}) gewechselt.')
                            ag.actual_route_cost += 0 # Was soll es Kosten seine Route zu ändern; noch 0
                            ag.route_changes += 1 # ANzahl an Routenänderungen

                    # Falls zu viele Route Changes gibt failt der Agent
                    if ag.route_changes > 3: # darf max. 3 mal seine Route ändern
                        print(f'Agent {ag.ID} wollte öfter als 3 mal seine Route ändern!')
                        ag.fail('COST')
                        continue

                # Knoten ist nicht disruptet:
                if mg.node_disrupted[standort] == False: # Abfrage ob Knoten disrupted ist
                    if service_rate[standort] >= ladung: # falls Servicerate ausreicht -> Agent kann abgefertigt werden
                        service_rate[standort] = service_rate[standort] - ladung
                        # Angekommen -> Aus Netzwerk und queue entfernen
                        if standort == ag.dest:
                            ag.reach_destination() # um den Rest kümmert sich reach_destination()
                        else:
                            # Abgefertigt, aber noch nicht am Zielknoten angekommen
                            print(f'Agent: {ag.ID}, Standort: {ag.so}, Destination: {ag.dest}, Route: {ag.route}')
                            next_SO = ag.route['path'][1]
                            pfad = (standort, next_SO, 0)  # pfad = nächste Kante des Agenten

                            # Perfekter Agent failt, wenn Kosten = inf, oder disruption des Zielknotens länger dauert als
                            # er für die Kante braucht; anonsten macht er sich auf den Weg
                            dis_ende_next_so = mg.node_dis[next_SO]
                            if mg.edge_total_cost[pfad] == float('inf') and (t + mg.edge_transport_time[pfad] - dis_ende_next_so) < 0:
                                ag.fail('COST')
                            # nicht perfekte Agenten machen sich ohne Überlegung auf den Weg zum nächsten Knoten
                            elif pfad in mg.edges:
                                # Agent aus Queue am ersten Knoten entfernen, und auf den Weg machen beginnt
                                if ag in mg.node_queue[ag.so]:
                                    mg.node_queue[ag.so].remove(ag)
                                    ag.so = pfad
                                    ag.at_edge = True
                                    ag.t_at_edge = 1

                                # Agent befindet sich bereits außerhalb der Queue -> Fehler (sollte im Normalfall nicht auftreten)
                                else:
                                    print('ERROR: ag not in list')

                                ag.state = "On Tour"
                                # Berechne Kosten des nächsten Pfades, diese werden dem Agenten dazuaddiert
                                kosten = mg.edge_total_cost[pfad]
                                ag.cost_next_edge = kosten
                                ag.actual_route_cost += kosten

                            else:
                                # Es gibt keinen Pfad zum nächsten Knoten (kann nicht auftreten, da keine Kanten entfernt werden)
                                ag.fail('PFAD')

                    # Service Rate reicht nicht aus! Agent kann nicht abgefertigt werden und muss am Knoten warten
                    # Dadurch erhögen sich die waiting_cost und er befindet sich in der Nodequeue und wird in
                    # update_edges, falls der Buffer dort nicht ausreicht, failen
                    elif service_rate[standort] < ladung:
                        ag.t_at_node += 1
                        ag.waiting_cost += 1

                # Knoten ist disrupted, aber dc_verändern=True
                # Verhalten sehr ähnlich wie bei einem nicht disrupteten Knoten, deshalb keine Kommentare (oben)
                elif dc_verändern==True:
                    if service_rate[standort] >= ladung:
                        service_rate[standort] = service_rate[standort] - ladung
                        if standort == ag.dest:
                            ag.reach_destination()
                        else:
                            print('SO:', ag.so, 'DEST:', ag.dest, 'R:', ag.route)
                            next_SO = ag.route['path'][1]
                            pfad = (standort, next_SO, 0)

                            dis_ende_next_so = mg.node_dis[next_SO]
                            if mg.edge_total_cost[pfad] == float('inf') and (t + mg.edge_transport_time[pfad] - dis_ende_next_so) < 0:
                                ag.fail('COST')

                            elif pfad in mg.edges:
                                if ag in mg.node_queue[ag.so]:
                                    mg.node_queue[ag.so].remove(ag)
                                    ag.so = pfad
                                    ag.at_edge = True
                                    ag.t_at_edge = 1

                                else:
                                    print('ERROR: ag not in list')

                                ag.state = "On Tour"
                                kosten = mg.edge_total_cost[pfad]
                                ag.cost_next_edge = kosten
                                ag.actual_route_cost += kosten

                            else:
                                ag.fail('PFAD')

                    # keine Abfertigung möglich
                    elif service_rate[standort] < ladung:
                        ag.t_at_node += 1
                        ag.waiting_cost += 1

                # Knoten ist disruptet und dc_verändern = False
                # alle Agenten hier befinden sich also an einem disrupted Knoten und failen deshalb
                else:
                    ag.fail('DISRUPT')

            # Fallunterscheidung (2.Fall) Agenten betrachtet, die sich auf Kanten befinden:
            elif ag.at_edge == True:
                ed = ag.so
                time_max = mg.edge_transport_time[ed]  # maximale Zeit auf der Kante, bestimmt durch Eigenschaft in Layern
                ag.t_at_edge_max = time_max
                if time_max > ag.t_at_edge:
                    # Transportzeit auf Kante noch nicht abgeschlossen
                    ag.t_at_edge += 1

                else:
                    # Transportzeit auf Kante abgeschlossen -> von Kante entfernen und zum nächsten Knoten gehen
                    ag.go_next()
                    # Kosten der Route für Agent updaten
                    # Kosten der Route wird dabei immer nur für den verbleibenden Weg betrachtet
                    ag.route['cost'] -= mg.edge_total_cost[ed]

            ag.display_agent()

        # erneutes Aufrufen von update_edges() da sich die Standorte der Agenten und damit die Kantenkosten verändert haben
        # wichtig für gleich neu erzeugten Agenten, damit sie ihre Route nach dem neuesten Stand wählen können
        mg.update_edges(mg.agent_list, bool_perf_ag=bool_perf_ag, dc_verändern=dc_verändern, dc_quotient=dc_quotient)

        # Listen für Plot nach jeder Periode auffüllen
        agents_per_timestep.append(mg.agent_count)
        delivered_agents_per_timestep.append(mg.agents_delivered_count)
        f_disrupt_agents_per_timestep.append(mg.count_failed_disrupt)
        f_no_next_agents_per_timestep.append(mg.count_failed_no_next)
        f_pfad_agents_per_timestep.append(mg.count_failed_pfad)
        f_queue_agents_per_timestep.append(mg.count_failed_queue)
        f_gen_full_buffer_per_timestep.append(mg.count_failed_gen_full_buffer)
        f_cost_per_timestep.append(mg.count_failed_cost)

    # Netzwerk in Konsole und in CSV darstellen
    mg.display_network_konsole()
    mg.display_network(n_timesteps, bool_perf_ag, ag_gen_laufzeit, gen_at_dis_node, lyr_similar_load, dv, dc_verändern, dc_buffer, dc_service_rate, dc_aufhebung, dt, dp)

    # # folgender auskommentierter Code funktioniert noch nicht reibungsfrei
    # # es sollte ein Plot zur Kostenübersicht der Agenten dargestellt werden

    # print('Achtung bei der Auswertung. Es handelt sich um Mittelwerte, die ausreßersensitiv sind. Außerdem hängen die'
    #       ' dargstellten Kosten stark von den zufällig generierten Routen ab und den Kosten, die zwischen den Layern'
    #       'variieren.')
    # # Route Kosten printen
    # pd.set_option('display.max_columns', 500)
    # df = pd.DataFrame(mg.route_cost_comp,
    #                   columns=['Lyr-ID (ag_gen)', 'Initial Edge Cost', 'Actual Cost', 'Waiting Cost', 'Total'])
    # df = df.groupby('Lyr-ID (ag_gen)').agg(
    #     {'Lyr-ID (ag_gen)': 'size', 'Initial Edge Cost': 'mean', 'Actual Cost': 'mean',
    #      'Waiting Cost': 'mean', 'Total': 'mean'}).rename(columns={'Lyr-ID (ag_gen)': 'count Layer_ID',
    #                                                                'Initial Edge Cost': 'init_mean',
    #                                                                'Actual Cost': 'actual_mean',
    #                                                                'Waiting Cost': 'wait_mean',
    #                                                                'Total': 'total_mean'}).reset_index()
    # print(df)
    # df['Layer-ID (Agents arrived per layer)'] = df['Lyr-ID (ag_gen)'].astype(str) + " (" + df['count Layer_ID'].astype(str) + ")"
    # del df['count Layer_ID']
    # del df['Lyr-ID (ag_gen)']
    # df_plot = df.plot.bar(x='Layer-ID (Agents arrived per layer)', title="Mean Costs per Agent")
    # plt.tight_layout()
    # plt.show()

    # Plots erstellen
    plot_all(mg)

    print("")
    print("============================================")
    print("")

# Laufzeit ermitteln
time_ende = time.time()
time_all = time_ende - time_start
print('GESAMTZEIT:', '{:5.3f}s'.format(time_all))

# Prozesslaufzeit ermitteln
time_ende_proc = time.process_time()
time_all_proc = time_ende_proc - time_start_proc
print('SYSTEMZEIT:', '{:5.3f}s'.format(time_all_proc))