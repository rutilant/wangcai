#coding=utf-8
import logging
import socket
import time

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      InlineQueryResultArticle, InputTextMessageContent,
                      KeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          InlineQueryHandler, MessageHandler, Updater)
from tinydb import Query, TinyDB

TOKEN=''
REQUEST_KWARGS={
    'proxy_url': 'http://127.0.0.1:1080',
}
updater = Updater(TOKEN, request_kwargs=REQUEST_KWARGS)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

rule_table = TinyDB('rule_table.json')
history = TinyDB('history.json')
pointboard =TinyDB('pointboard.json')
query_db = Query()

def start(bot, update):
    logging.info('收到指令/start')
    bot.send_message(chat_id=update.message.chat_id, text="我是旺财，我是一个没有感情的尿床精。")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()

# 复读机功能
def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text+"！")

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

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
    logging.info('button lists created')
    logging.info('categories:'+str(category))
    # 提取类别列表，返回类别给 callback query
    cat_button_list = []
    for cat in category.keys():
        cat_button_list.append(InlineKeyboardButton(cat, callback_data=str(1000+category.get(cat))))
    logging.info('category button created')
    reply_markup = InlineKeyboardMarkup(build_menu(cat_button_list, n_cols=2))
    bot.send_message(chat_id=update.message.chat_id, text="首先选择类别", reply_markup=reply_markup)

point_handler = CommandHandler('done', show_cat_list)
dispatcher.add_handler(point_handler)


def show_ev_list(bot,update,category):
    button_list = button_lists[category]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
    bot.send_message(chat_id=update.effective_chat.id, text="你做了什么？", reply_markup=reply_markup)    

# callback 处理，菜单按钮反馈
def point_up_action(bot,update):
    query = update.callback_query.data
    logging.info('callback query received:'+query)
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

callback_handler = CallbackQueryHandler(point_up_action)
dispatcher.add_handler(callback_handler)


def add_point(update,eventid):
    userid = update.effective_user.id
    user_status = pointboard.get(query_db.userid == userid)
    event = rule_table.get(doc_id = eventid)
    logging.info('current event:'+str(event))
    if user_status != None:
        # 增加积分
        pointboard.update({'current_points': (user_status['current_points']+event['point']),'recent_change': event['point']}, query_db.userid == userid)
    else:
        # 添加新用户
        logging.info('new user'+str(userid))
        pointboard.insert({'userid':userid, 'username':update.effective_user.name, 'current_points':event['point'], 'recent_change':event['point'], 'user_chat_id':update.effective_chat.id, 'subscribe':False})
    # 写历史记录
    history.insert({'userid':userid,'event':event['event'],'change':event['point'], 'update_time':time.asctime( time.localtime(time.time()) )})
    logging.info('history updated')
    # 读取改动过的记录
    user_status = pointboard.get(query_db.userid == userid)
    logging.info('user updated:'+str(user_status))
    showtext = update.effective_user.name + ' 进行了' + event['event'] + '操作并获得了' + str(event['point']) + '点积分，目前的总积分是' + str(user_status['current_points']) + '。'
    return showtext


def notification(bot,update):
    userid = update.effective_user.id
    user_status = pointboard.get(query_db.userid == userid)
    if user_status['subscribe']:
        bot.send_message(chat_id=update.effective_chat.id, text='已关闭订阅通知，现在你不会收到其他人的积分变动信息。')
    else:
        bot.send_message(chat_id=update.effective_chat.id, text='已开启订阅通知，现在你会收到所有人的积分变动信息。')
        logging.info(userid+'is now a subscriber')
    pointboard.update({'subscribe':not user_status['subscribe']},query_db.userid == userid)
sub_handler = CommandHandler('subscribe', notification)
dispatcher.add_handler(sub_handler)


# 对未知指令
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="喵喵喵？")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


updater.idle()
# updater.stop()