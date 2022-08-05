# Introduction:

[AP2 final project in GCED, built in 2021]

This file will help understand the iGo.py and bot.py files and what they do. It also explains the use of every command available and the errors that may occur.

### iGo bot
Implementation of a telegram bot that provides car directions around Barcelona.

### Telegram bot
App that can be executed in Telegram. The users can interact with it by sending messages or commands. It is possible to create your own bot using an API token.

### Bot utility
This bot provides directions around Barcelona. It shows the shortest path towards user's destination. The congestions are updated every five minutes.

# Index
- [Requirements](#Requirements)
- [Barcelona Graph](#Barcelona_Graph)
  - [Data](##Data)
  - [Building the igraph](##Building_the_igraph)
- [Functions in iGo.py](#Functions_in_iGo.py)
- [Bot commands](#Bot_commands)
- [Functions in bot.py](#Functions_in_bot.py)
- [Errors](#Errors)

# Requirements
*requirements.txt.txt*  contains all the modules that need to be installed (in the versions needed) so that there is no malfunction with the bot.

You can install them with the command:
```
pip3 install -r requirements.txt
```

# Barcelona Graph
We developed this task using Open Street Map that allows us to download the graph of Barcelona. The streets are the edges and the nodes their intersections. Each node and edge contain different attributes. The attributes we find in edges are more important as we find the street's max speed and length. There are some edges that do not have a speed attribute residential we give them a value of 20km/h.

We modified this graph so the bot finds the shortest path between two nodes taking into account the congestions of each street.

## Data

The data we use for the highways and their congestion is found in csv format:

[Highways](https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv)

[Congestions](https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download)

The Barcelona graph is grabbed using osmnx.


## Building the igraph
The igraph is an intelligent version of the Barcelona graph with an added attribute to the edges named itime.
Itime is the approximated time it takes to traverse the street depending on the congestion.
To calculate it first we need to read the streets and congestions from https://opendata-ajuntament.barcelona.cat/data/ca/dataset/trams and
https://opendata-ajuntament.barcelona.cat/data/ca/dataset/transit-relacio-trams.
We can see that every street has an id, this helps us to relate them with their congestions. Also the congestions tables have the
following columns: current traffic and expected traffic. We only use the current traffic as it is the most accurate. Here we have a table with congestions and the factor we have decided to give them.
0 to 6:
- 0: no data | factor: 1.2
- 1: very fluid | factor: 1
- 2: fluid | factor: 1.05
- 3: dense | factor: 1.2
- 4: very dense | factor: 1.4
- 5: traffic jam | factor: 1.7
- 6: cut | factor: 1e6

For each congestion we have decided on a factor (bigger the value bigger the factor) and then we calculate the itime by dividing the length by the average speed (in some cases the maximum speed of the edge contains two values so we calculate the average) multiplied by the factor:
length/average_speed*factor

Some clarifications about the factors:
- It can be seen that the factor of 0 is the same as the factor of dense, that's because when there is no data of the congestion we consider that they are not very influencing roads so the factor is the middle term.
- The value 6 has 1e6 factor so the itime is huge compared to the others.

The itime is calculated for every edge and the added to their attributes.

Because of the updates in the congestions, we also need to update the intelligent graph every five minutes.

# Functions in iGo.py

Here we have the functions in the iGo.py file as a complement of the explanation made before.

- ```exists_graph``` : Returns True if file exists and is a .graph file, returns False otherwise.
                       Parameters: graph_filename.

- ```download_graph```: Returns a graph object from a place, edges are the different streets and their weight indicates their length.
                        Parameters: place (in this case Barcelona).

- ```save_graph```: Saves a graph object into a .graph file.
                    Parameters: graph and graph_filename.

- ```load_graph```: Returns a graph objects from a .graph file.
                    Parameters: graph_filename.

- ```plot_graph```: Plots a graph located in a .graph file.
                    Parameters: graph_filename.

- ```download_highways```: Reads a CSV file stored online and returns a list of highways. Each highway is formed
                           by an id, a description and a tuple with the beginning and ending coordinates.
                           Parameters: url.

- ```plot_highways```: Creates/modifies a png file with a map of Barcelona and with the highways on
                       the highway list drawn.
                       Parameters: highway_list, png file, size.

- ```download_congestions```: Reads a file stored online and returns a list of congestions. Each congestion is
                              formed by an id, a time, a transit and a future transit.
                              Parameters: url.

- ```plot_congestions```: Creates/modifies a png file with a map of Barcelona and with the highways on the
                          highway_list drawn with colors varying depending on the congestion.
                          Parameters: highway_list, congestion_list, fileName and size.

- ```spread_congestions```: Spreads the congestions from the list to the graph.
                            Parameters: graph, highway_list and congestion_list.

- ```calculate_itime```: Calculates itime from the three attributes given. Congestion is a value from 0 to 6.
                         Parameters: congestion, speed and length.

- ```add_itime```: adds the itime to the edges of the graph.
                   Parameters: graph.

- ```build_igraph```: builds an intelligent graph taking into account the congestions of the highways.
                      Parameters: graph, highway_list and congestion_list.

- ```get_shortest_path_with_ispeeds```: gets the shortest path from the origin to the destination considering the itime.
                                        Parameters: graph, origin, destination.

- ```plot_path```: Creates/modifies a png file with a map of Barcelona marking the path given.
                   Parameters: graph, path, fileName and size.

- ```create_igraph_file```: builds an intelligent graph and saves it into a graph file.
                            Parameters: None.

- ```update_igraph_file```: updates the intelligent graph.
                            Parameters: igraph and files.

- ```coordinates```: provides coordinates of a location.
                    Parameters: location.


# Bot commands
- ```/Start``` : initializes the bot.

- ```/Help``` : Gives a list of the commands available.

- ```/Authors``` : name of the bot's authors.

- ```/pos```: Creates a false location and can recieve coordinates or the name's place.

- ```/where```: gives the user's current location.

- ```/go```: Gives the shortest path from user's location to destiny.

The user simply has to send his location so the bot can obtain what will be the source of the path and then
use the command /go as follows: /go destination. The bot will obtain the text of destination, transform it into
coordinates and then send a photo whit the shortest path between source an destination drawn.
In case there are some doubts the user just has to send /help and the bot will reply
with a list of the commands available.

# Functions in bot.py
Here are the functions of the bot.py file:

- ```send_telegram_message```: the bot sends a message.
                               Parameters: text, update and context.

- ```send_telegram_photo```: the bot sends a photo.
                             Parameters: file, update and context.      
- ```start```: Initiates conversation and introduces itself.
               Parameters: update and context.

- ```help```: Gives the commands available.
              Parameters: update and context.

- ```authors```: Shows the name of the authors and their emails.
                 Parameters: update and context.

- ```location```: Saves the user's location.
                  Parameters: update and context.

- ```where```: Sends an and with a marker showing the user's location.
               Parameters: update and context.

- ```show_path```: Sends an image with the shortest path between the origin and destination drawn.
                   Parameters: update and use_context.

- ```go```: Gets the source and the destination and sends a photo with the shortest path between them drawn.
            Parameters: update and context.

- ```pos```: Saves the user's location. Location must be in either text or coordinates.
             Parameters: update and context.

- ```update_igraph```: Updates igraph file.
                      Parameters: context.

# Errors
- Bot will not provide path if no original location is given or no destination is given.
- If the given destination is not found or is not in Barcelona bot will not show the path.
