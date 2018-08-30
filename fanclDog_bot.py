#!/usr/bin/python3
#coding=utf-8
import argparse
import logging
import socket
import time
import yaml

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      InlineQueryResultArticle, InputTextMessageContent,
                      KeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          InlineQueryHandler, MessageHandler, Updater)
from tinydb import Query, TinyDB

AUTHTOKEN = None
REQUEST_KWARGS=None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

# y = open('./fanclDog.yaml', encoding='UTF-8')
# rules = yaml.load(y)['rules']
rule_table = TinyDB('rule_table.json')
history = TinyDB('history.json')
pointboard =TinyDB('pointboard.json')
query_db = Query()

def start(bot, update):
    logger.info('收到指令/start')
    bot.send_message(chat_id=update.message.chat_id, text='我是旺财，我是一个没有感情的尿床精。')


# 复读机功能
def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text+'！')


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

# I've done something 指令处理
button_lists = []
def show_cat_list(bot, update):
    category = {}
    i = 0
    # 生成完整 button list
    for ev in iter(rule_table):
        # print(ev)
        if ev['category'] in category:
            i = category.get(ev['category'])
            button_lists[i].append(InlineKeyboardButton(ev['event'], callback_data=ev.doc_id))
        else:
            button_list = [InlineKeyboardButton(ev['event'], callback_data=ev.doc_id)]
            button_lists.append(button_list)
            category[ev['category']] = len(button_lists)-1
    logger.info('button lists created')
    logger.info('categories:'+str(category))
    # 提取类别列表，返回类别给 callback query
    cat_button_list = []
    for cat in category.keys():
        cat_button_list.append(InlineKeyboardButton(cat, callback_data=str(1000+category.get(cat))))
    logger.info('category button created')
    reply_markup = InlineKeyboardMarkup(build_menu(cat_button_list, n_cols=2))
    bot.send_message(chat_id=update.message.chat_id, text='首先选择类别', reply_markup=reply_markup)


def show_ev_list(bot,update,category):
    button_list = button_lists[category]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
    bot.send_message(chat_id=update.effective_chat.id, text='你做了什么？', reply_markup=reply_markup)    

# callback 处理，菜单按钮反馈
def point_up_action(bot,update):
    query = update.callback_query.data
    logger.info('callback query received:'+query)
    # print(query)
    if int(query) >= 1000:
        category = int(query)-1000
        show_ev_list(bot,update,category)
    else:
        message = add_point(update,int(query))
        current_chat_id = update.effective_chat.id
        subscribers = pointboard.search(query_db.subscribe == True)
        bot.send_message(chat_id=current_chat_id, text=message)
        for mem in subscribers:
            if mem['user_chat_id'] != current_chat_id:
                bot.send_message(chat_id=mem['user_chat_id'], text=message)


def add_point(update,eventid):
    userid = update.effective_user.id
    user_status = pointboard.get(query_db.userid == userid)
    event = rule_table.get(doc_id = eventid)
    logger.info('current event:'+str(event))
    if user_status:  # is not none
        # 增加积分
        pointboard.update({'current_points': (user_status['current_points']+event['point']),'recent_change': event['point']}, query_db.userid == userid)
    else:
        # 添加新用户
        logger.info('new user'+str(userid))
        pointboard.insert({'userid':userid, 'username':update.effective_user.name, 'current_points':event['point'], 'recent_change':event['point'], 'user_chat_id':update.effective_chat.id, 'subscribe':False})
    # 写历史记录
    history.insert({'userid':userid,'event':event['event'],'change':event['point'], 'update_time':time.asctime( time.localtime(time.time()) )})
    logger.info('history updated')
    # 读取改动过的记录
    user_status = pointboard.get(query_db.userid == userid)
    logger.info('user updated:'+str(user_status))
    showtext = update.effective_user.name + ' 进行了' + event['event'] + '操作并获得了' + str(event['point']) + '点积分，目前的总积分是' + str(user_status['current_points']) + '。'
    return showtext


def notification(bot,update):
    userid = update.effective_user.id
    user_status = pointboard.get(query_db.userid == userid)
    if user_status['subscribe']:  # true
        bot.send_message(chat_id=update.effective_chat.id, text='已关闭订阅通知，现在你不会收到其他人的积分变动信息。')
    else:
        bot.send_message(chat_id=update.effective_chat.id, text='已开启订阅通知，现在你会收到所有人的积分变动信息。')
        logger.info(userid+'is now a subscriber')
    pointboard.update({'subscribe':not user_status['subscribe']},query_db.userid == userid)


# 对未知指令
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='喵喵喵？')


def startFromCLI():
    global AUTHTOKEN, REQUEST_KWARGS
    parser = argparse.ArgumentParser()
    parser.add_argument('auth', type=str, help='The Auth Token given by Telegram''s @botfather')
    parser.add_argument('-p','--proxy', type=str, default='http://127.0.0.1:1080', help='Proxy url used for http communication.')
    parser.add_argument('-l','--llevel', default='info', choices=['debug','info','warn','none'], 
                        help='Logging level for the logger, default = info')
    
    logLevel = {'none':logging.NOTSET,'debug':logging.DEBUG,'info':logging.INFO,'warn':logging.WARNING}
    
    args = parser.parse_args()
    logger.setLevel(logLevel[args.llevel])
        
    AUTHTOKEN = args.auth
    if args.proxy:
        REQUEST_KWARGS = {
            'proxy_url': args.proxy,
        }


def main():
    updater = Updater(AUTHTOKEN, request_kwargs=REQUEST_KWARGS)
    dispatcher = updater.dispatcher
    # /start
    dispatcher.add_handler(CommandHandler('start', start))
    # /done
    dispatcher.add_handler(CommandHandler('done', show_cat_list))
    # /subscribe
    dispatcher.add_handler(CommandHandler('subscribe', notification))
    # callback
    dispatcher.add_handler(CallbackQueryHandler(point_up_action))
    # any text
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    # unknown command
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()
    # updater.stop()

if __name__ == '__main__':
    startFromCLI()
    main()
