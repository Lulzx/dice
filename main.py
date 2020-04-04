#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
from itertools import chain
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler)

logging.basicConfig(format='%(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

GAME_STATE = False
players = {}
group_id = -1001250957853
game_values = {}

def start(update, context):
    update.message.reply_text('henlo frens, welcome to the dice game!\nsend /begin to get started.')


def help(update, context):
    update.message.reply_text('Help!')


def dicehandler(update, context):
    global group_id
    global game_values
    dice_value = update.message.dice.value
    user_id = update.message.from_user.id
    if GAME_STATE:
        game_values[user_id] = value
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


def scenehandler(update, context):
    global GAME_STATE
    global group_id
    global game_values
    text = update.message.text
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    user_name = update.message.from_user.first_name
    # fetch, validate, process and add
    if "/begin" in text:
        GAME_STATE = True
        text = "The game is going to start"
        keyboard = [[InlineKeyboardButton("Join the game", callback_data=str(user_id))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=group_id, text=text, reply_markup=reply_markup)
        context.bot.send_message(chat_id=group_id, text="waiting for members to join..")
        for i in range(5, 0, -1):
            text = i
            time.sleep(1)
            context.bot.edit_message_text(chat_id=group_id, message_id=message_id+2, text=text)
        global players
        context.bot.edit_message_text(chat_id=group_id, message_id=message_id+2, text="starting the game with {} players..".format(len(list(players.keys()))))
        context.bot.send_message(chat_id=group_id, text="Throw your dices!")
        for i in range(5):
            time.sleep(1)
        winners = {}
        for key, value in game_values.items():
            if value not in winners: 
                winners[value] = [key] 
            else: 
                winners[value].append(key)
        final = context.bot.send_dice(chat_id=group_id)
        time.sleep(1)
        value = final.dice.value
        winners = winners[value]
        len_winners = len(winners)
        if len_winners > 1:
            string = "🎉 List of winners:\n"
            for n, winner in enumerate(winners):
                if n < len_winners - 1:
                    string += "├ " + winner + "\n"
                else:
                    string += "└ " + winner
        else:
            string = winners[0] + " is the winner! 🥳"
        context.bot.send_message(chat_id=group_id, text=string)
    elif text == "/cancel":
        GAME_STATE = False
        text = "The game has been dismissed."
        context.bot.send_message(chat_id=group_id, text=text)
    elif text == "/dice":
        message = context.bot.send_dice(chat_id=group_id)
        time.sleep(1)
        value = message.dice.value
        context.bot.send_message(chat_id=group_id, text=value)
    elif text == "/check":
        if GAME_STATE:
            text= "✅ The game is in progress!"
        else:
            text = "⛔️ The game has not started yet."
        context.bot.send_message(chat_id=group_id, text=text)
    elif text == "/reset":
        GAME_STATE = False
        players = {}
        context.bot.send_message(chat_id=chat_id, text="☑️ Reset done!")


def query_handler(update, context):
    global group_id
    global players
    query = update.callback_query
    user_name = query.from_user.first_name
    user_id = query.from_user.id
    if user_id in list(players.keys()):
        text="You are already in the game! 😉"
        context.bot.answer_callback_query(query.id, text=text, show_alert=False)
        return
    text = "You have 15 seconds to join.\n"
    text += "You'll need at least two other friends in order to play.\n"
    text += "Player List:\n"
    text += list_builder(user_id, user_name)
    keyboard = [[InlineKeyboardButton("Join the game", callback_data=str(user_id))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=text, reply_markup=reply_markup)
    context.bot.send_message(chat_id=group_id, text=f"{user_name} joined the session.")


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    try:
        TOKEN = sys.argv[1]
    except IndexError:
        TOKEN = os.environ.get("TOKEN")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, scenehandler))
    dp.add_handler(CallbackQueryHandler(query_handler))
    dp.add_handler(MessageHandler(Filters.dice, dicehandler))
    dp.add_error_handler(error)
    updater.start_polling()
    logger.info("Ready to rock..!")
    updater.idle()


if __name__ == '__main__':
    main()
