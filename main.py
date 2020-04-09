#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
import emoji
from itertools import chain
import functools
from functools import wraps
import operator
from humanfriendly import format_size, parse_size
from tinydb import TinyDB, Query
from tinydb.operations import increment, decrement, add, subtract, delete, set
from tabulate import tabulate
import numpy as np
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext.dispatcher import run_async
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler)
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

db = TinyDB('db.json')
player = Query()

LIST_OF_ADMINS = [691609650]
GAME_STATE = False
wait_for_players = False
players = {}
group_id = -1001250957853
nParticipants = 0
game_values = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
participated_text = "this game has end, start a new game."

def start(update, context):
    update.message.reply_text('henlo frens, welcome to the dice game!\nsend /begin to get started.')


def help(update, context):
    update.message.reply_text('Ask your frens in the group!')


def dicehandler(update, context):
    global game_values
    global players
    global wait_for_players
    if wait_for_players:
        dice_value = update.message.dice.value
        user_name = update.message.from_user.first_name
        user_id = update.message.from_user.id
        if str(user_id) not in str(players):
            return
        if GAME_STATE:
            game_values[dice_value].extend([[user_name, user_id]])
            del players[user_id]
            return


def list_builder(user_id, user_name):
    global players
    players[user_id] = user_name
    players_list = list(players.values())
    string = ""
    len_players = len(players_list)
    if len_players > 1:
        for n, player in enumerate(players_list):
            if n < len_players - 1:
                string += "├ " + player + "\n"
            else:
                string += "└ " + player
    else:
        string += "└ " + players_list[0]
    return string


@run_async
def scenehandler(update, context):
    global GAME_STATE
    global group_id
    global game_values
    global players
    global participated_text
    global wait_for_players
    global nParticipants
    try:
        text = update.message.text.lower()
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        message_id = update.message.message_id + 1
        user_name = update.message.from_user.first_name
    except AttributeError:
        return
    # fetch, validate, process and add
    if text.startswith(("/begin", "/again")):
        if GAME_STATE:
            text = "The game is in progress.."
            context.bot.send_message(chat_id=group_id, text=text)
            return
        reset()
        GAME_STATE = True
        while GAME_STATE:
            text = "The game is going to start"
            keyboard = [[InlineKeyboardButton("Join the game", callback_data=str(user_id))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=group_id, text=text, reply_markup=reply_markup)
            context.bot.send_message(chat_id=group_id, text="waiting for members to join..")
            for i in range(10, 0, -1):
                time.sleep(1)
            try:
                context.bot.edit_message_text(chat_id=group_id, message_id=message_id, text=participated_text)
            except:
                pass
            participants = list(players.keys())
            nParticipants = len(participants)
            if nParticipants == 0:
                context.bot.send_message(chat_id=group_id, text="Nobody participated :(")
                reset()
                return
            context.bot.send_message(chat_id=group_id, text="starting the game with {} players..".format(nParticipants))
            wait_for_players = True
            context.bot.send_message(chat_id=group_id, text="Throw your dice!")
            for i in range(10):
                time.sleep(1)
            context.bot.send_message(chat_id=group_id, text="Time's up, over!")
            time.sleep(1)
            final = context.bot.send_dice(chat_id=group_id)
            time.sleep(1)
            dice_value = final.dice.value
            string = "No winners this time :("
            try:
                winners = [v for k,v in game_values.items() if k > dice_value or k == 6]
                winners = functools.reduce(operator.iconcat, list(filter(None, winners)), [])
                len_winners = len(winners)
                winners_name = list(np.array(winners).T[0])
                winners_id = list(np.array(winners).T[1])
                winners_id = list(map(int, winners_id))
                time.sleep(1)
                losers_id = list(filter(lambda x: x not in winners_id, participants))
                scores(winners_id, winners_name, nParticipants, losers_id)
                if len_winners > 1:
                    string = "🎉 List of winners:\n"
                    for n, winner in enumerate(winners_name):
                        if n < len_winners - 1:
                            string += "├ " + str(winner) + "\n"
                        else:
                            string += "└ " + str(winner)
                elif len_winners == 1:
                    string = str(winners_name[0]) + " is the winner! 🥳"
            except IndexError:
                string = "No winners this time :("
            except KeyError:
                string = "No winners this time :("
            context.bot.send_message(chat_id=group_id, text=string)
            if string.endswith(":("):
                reset()
                return
            table = []
            headers = ["Name", "Brain RAM"]
            for i in range(len_winners):
                name = winners_name[i]
                user_id = winners_id[i]
                try:
                    score = db.search(player.user_id == user_id)[0]['score']
                    score = str(format_size(parse_size(str(score))))
                except IndexError:
                    if len_winners == 1:
                        reset()
                        return
                    continue
                table.extend([[name, score]])
            text = "```{}```".format(str(tabulate(table, headers, tablefmt="presto", floatfmt=".2f")))
            context.bot.send_message(chat_id=group_id, text=text, parse_mode=ParseMode.MARKDOWN)
            reset()
    elif text == "/cancel":
        GAME_STATE = False
        text = "The game has been dismissed."
        context.bot.send_message(chat_id=group_id, text=text)
    elif text == "/dice":
        message = context.bot.send_dice(chat_id=group_id)
        time.sleep(1)
        value = message.dice.value
        context.bot.send_message(chat_id=group_id, text=value)
    elif text.startswith("/check"):
        if GAME_STATE:
            text= "✅ The game is in progress!"
        else:
            text = "⛔️ The game has not started yet."
        context.bot.send_message(chat_id=group_id, text=text)
    elif text == "/reset":
        reset()
        context.bot.send_message(chat_id=chat_id, text="☑️ Reset done!")
    elif text == "/info":
        text = "Total players: {}".format(len(db))
        context.bot.send_message(chat_id=group_id, text=text)
    elif text == "/leaderboard":
        table = []
        undecorated = db.all()
        result = sorted(undecorated, key=operator.itemgetter('score'), reverse=True)
        for i in range(len(result)):
            name = result[i]['name']
            score = (result[i]['score'])
            score = str(format_size(parse_size(str(score))))
            table.extend([[name, score]])
        headers = ["Name", "Brain RAM"]
        text = "*Leaderboard*\n```{}```".format(str(tabulate(table, headers, tablefmt="presto", floatfmt=".2f")))
        context.bot.send_message(chat_id=group_id, text=text, parse_mode=ParseMode.MARKDOWN)


def reset():
    global GAME_STATE
    global players
    global game_values
    global participated_text
    global wait_for_players
    GAME_STATE = False
    wait_for_players = False
    players = {}
    game_values = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    participated_text = "this game has end, start a new game."
    return


def scores(winners, names, nParticipants, losers):
    total_winners = len(winners)
    base_reward = 10
    for winner in winners:
        current = db.search(player.user_id == winner)
        if current != []:
            winning_streak = int(current[0]['winning_streak']) + 1
            if winning_streak == 0 or winning_streak < 0:
                winning_streak = 1
                db.update(set('winning_streak', 0), player.user_id == winner)
            final_score = round((abs(winning_streak)/winning_streak)*nParticipants*(base_reward/total_winners)**(winning_streak), 3)
            db.update(increment('winning_streak'), player.user_id == winner)
            db.update(add('score', final_score), player.user_id == winner)
        else:
            name = names[winners.index(winner)]
            name = emoji.get_emoji_regexp().sub(r'', name)
            db.insert({'name': str(name), 'user_id': winner, 'score': base_reward, 'winning_streak': 1})

    for loser in losers:
        current = db.search(player.user_id == loser)
        if current != []:
            winning_streak = int(current[0]['winning_streak']) - 1
            if winning_streak == 0:
                final_score = round(nParticipants*total_winners*base_reward, 2)
                db.update(subtract('score', final_score), player.user_id == loser)
                return
            final_score = round((abs(winning_streak)/winning_streak)*nParticipants*(base_reward/total_winners)**(winning_streak), 3)
            db.update(set('winning_streak', 0), player.user_id == loser)
            score = db.search(player.user_id == loser)[0]['score']
            if score + final_score < 0 or score - final_score < 0:
                final_score = 0
            db.update(subtract('score', final_score), player.user_id == loser)


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)

    return wrapped


@restricted
def backup(update, context):
    update.message.reply_document(document=open('db.json', 'rb'))


@restricted
def backup_handler(update, context):
    file = context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    os.remove(file_name)
    file.download(file_name)
    update.message.reply_text(text="Alright! I have uploaded the backup.")


def query_handler(update, context):
    global group_id
    global players
    global GAME_STATE
    query = update.callback_query
    user_name = query.from_user.first_name
    user_id = query.from_user.id
    if user_id in list(players.keys()):
        text="You are already in the game! 😉"
        context.bot.answer_callback_query(query.id, text=text, show_alert=False)
        return
    if GAME_STATE == False:
        text="The game has already end before. start a new one. 😛"
        context.bot.answer_callback_query(query.id, text=text, show_alert=True)
        return
    text = "You have 10 seconds to join.\n"
    text += "You'll need at least two other friends in order to play.\n"
    text += "Player List:\n"
    text += list_builder(user_id, user_name)
    keyboard = [[InlineKeyboardButton("Join the game", callback_data=str(user_id))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    global participated_text
    participated_text = text
    query.edit_message_text(text=text, reply_markup=reply_markup)


def error(update, context):
    global group_id
    try:
        logger.warning('Update "%s" caused error "%s"', update, context.error)
    except BadRequest:
        context.bot.send_message(chat_id=group_id, text="Sorry, An error occured. Start again!")
        logger.warning('bad request')
    except TimedOut:
        logger.warning('slow internet')
    except NetworkError:
        logger.warning('no network')


def main():
    try:
        TOKEN = sys.argv[1]
    except IndexError:
        TOKEN = os.environ.get("TOKEN")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.private, scenehandler))
    dp.add_handler(CallbackQueryHandler(query_handler))
    dp.add_handler(MessageHandler(Filters.dice & ~Filters.forwarded, dicehandler))
    dp.add_handler(CommandHandler("backup", backup))
    dp.add_handler(MessageHandler(Filters.document, backup_handler))
    dp.add_error_handler(error)
    updater.start_polling()
    logger.info("Ready to rock..!")
    updater.idle()


if __name__ == '__main__':
    main()
