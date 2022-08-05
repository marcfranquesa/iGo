import igo
import json
import urllib
import os
import random
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from staticmap import StaticMap, CircleMarker, Line
TOKEN = 'XXXXXXXXXXX'


def send_telegram_message(text, update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text)


def send_telegram_photo(file, update, context):
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open(file, 'rb'))


def start(update, context):
    '''Initiates conversation and introduces itself.'''
    text = 'Hello! I am a direction giving bot, do /help for more information.'
    send_telegram_message(text, update, context)


def help(update, context):
    '''Shows the commands available.'''
    text = '''
    Here is a list with all commands and their description:
/start - starts the bot
/help - send a list with all available commands
/authors - name & email of the bot makers
/where - send a user's location
/go ___ - sends an image with the shortest path to the chosen destination

To save your location simply send it to the bot!
    '''
    send_telegram_message(text, update, context)


def authors(update, context):
    '''Shows the name of the authors and their emails.'''
    text = '''
Eduard Ramón Aliaga, eduard.ramon.aliaga@estudiantat.upc.edu

Marc Franquesa, marc.franquesa@estudiantat.upc.edu
    '''
    send_telegram_message(text, update, context)


def location(update, context):
    '''Saves the user's location.'''
    try:
        # Grabs latitude and longitude
        lat = update.message.location.latitude
        lon = update.message.location.longitude

        # Saves them in a user specific dictionary
        context.user_data['location'] = (lat, lon)
        send_telegram_message('Location has been saved.', update, context)
        print('Saved {}\'s location.'.format(update.effective_chat.first_name))

    except Exception as e:
        print(e)
        send_telegram_message('💣', update, context)


def where(update, context):
    '''Sends an image and with a marker showing the user's location.'''
    try:
        # Grabs location from a user specific dictionary
        lat, lon = context.user_data['location']

        # Creates png file and adds the marker
        file = '{}.png'.format(random.randint(1000000, 9999999))
        map = StaticMap(500, 500)
        map.add_marker(CircleMarker((lon, lat), 'red', 10))
        image = map.render()
        image.save(file)

        send_telegram_photo(file, update, context)
        os.remove(file)
    except:
        print(update.effective_chat.first_name, 'tried to show his location without sending it first.')
        send_telegram_message('Please send your location first.', update, context)


def show_path(update, context):
    '''Sends an image with the shortest path between
    the origin and destination drawn.'''
    user_name = update.effective_chat.first_name
    print(user_name + ' has started a route.')

    path = None
    source = context.user_data['location']

    # Returns None if no coords were found
    destination = igo.coordinates(update.message.text[4:])
    igraph = context.bot_data['igraph']

    user_path_file = user_name + '{}.png'.format(random.randint(1000000, 9999999))

    if destination is None:
        send_telegram_message('Could not find location "{}".'.format(update.message.text[4:]), update, context)
        print(user_name + ' did not provide a suitable destination.')
        return

    path = igo.get_shortest_path_with_ispeeds(igraph, source, destination)

    # If path was found plots it and sends it
    if path is not None:
        igo.plot_path(igraph, path, fileName=user_path_file)
        send_telegram_photo(user_path_file, update, context)
        os.remove(user_path_file)
        print(user_name + '\'s route is finished.')
        return

    # If for some reason no path was found
    # Can happen if destination coordinates are not in barcelona
    send_telegram_message('Could not provide path.'.format(destination), update, context)
    print(user_name + '\'s route could not be finished.')


def go(update, context):
    '''Gets the source and the destination and sends an image
    with the shortest path between them drawn. User must have
    provided an origin and a desired destination.'''
    text = update.message.text[4:]

    # Checks if user has submitted a destination
    if len(text) == 0:
        print(update.effective_chat.first_name, 'tried to get a path without sending a destination.')
        send_telegram_message('The command is /go <destination>', update, context)
        return

    # Checks if user has sent his location
    try:
        source = context.user_data['location']
        location_given = True
    except:
        location_given = False
        text = 'tried to get a path without sending his location first.'
        print(update.effective_chat.first_name, text)
        send_telegram_message('Please send your location first.', update, context)

    # Provides image with shortest path
    if location_given:
        show_path(update, context)


def pos(update, context):
    '''Saves the user's location. Location must be in
    either text or coordinates.'''
    text = update.message.text[5:]

    # Returns None if location was not found
    coords = igo.coordinates(text)

    if coords is not None:
        context.user_data['location'] = coords
        print('{}\'s location has been saved.'.format(update.effective_chat.first_name))
        send_telegram_message('Location has been saved.', update, context)
        return

    # In case no coordinates where found
    print('Did not find {}\'s submitted location.'.format(update.effective_chat.first_name))
    text = 'Could not find location "{}".'.format(text)
    send_telegram_message(text, update, context)


def update_igraph(context):
    '''Updates igraph file.'''
    igo.update_igraph_file(context.bot_data['igraph'], context.bot_data['highways'])


print('Booting up the bot.')

# Creates objects to work with telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
job_queue = updater.job_queue

dispatcher.bot_data['highways'], dispatcher.bot_data['igraph'] = igo.create_igraph()

# Indicates what functions correspond to each command
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('authors', authors))
dispatcher.add_handler(MessageHandler(Filters.location, location))
dispatcher.add_handler(CommandHandler('where', where))
dispatcher.add_handler(CommandHandler('go', go))
dispatcher.add_handler(CommandHandler('pos', pos))

# Updates igraph every 5 minutes
job_queue.run_repeating(update_igraph, interval=5*60, first=0.0)

# Boots the bot
print('Bot is now operational.')
updater.start_polling()
updater.idle()
