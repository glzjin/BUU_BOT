# -*- coding: utf-8 -*
import itchatmp

import utils, os
import buu_config
import buu_msg_handle
import buu_database
import sys
import buu_model
import buu_thread_keepalive
import buu_thread_card
import buu_thread_lib
import buu_command_dict

itchatmp.update_config(itchatmp.WechatConfig(
    token = buu_config.config.weixin_token,
    appId = buu_config.config.weixin_appid,
    appSecret = buu_config.config.weixin_appsecret,
    encryptMode = itchatmp.content.SAFE,
    encodingAesKey = buu_config.config.weixin_encoding_aeskey,))

menu = buu_config.config.wechat_menu

r = itchatmp.menu.create(menu)

@itchatmp.msg_register(itchatmp.content.EVENT)
def user_management(event):
    if event['Event']=='subscribe':
        return buu_command_dict.class_command_dict.step_0_tips('', '', 0)

@itchatmp.msg_register(itchatmp.content.TEXT)
def text_reply(msg):
    return msg_handler.msg_handle(msg)

def encrypt_passwords():
    import buu_model, buu_database
    database_op = buu_database.class_database_op()
    exist_cards = buu_model.class_model.Card.select()

    for card in exist_cards:
        database_op.save_card_info(card.user.id, card.user_name, card.password)

buu_model.class_model.init()

msg_handler = buu_msg_handle.class_msg_handle()

class_database_op = buu_database.class_database_op()
# class_database_op.flush_redis()

buu_thread_card.class_init_thread_supervisor()

buu_thread_lib.class_init_thread_supervisor()

buu_thread_keepalive.class_init_thread()

# encrypt_passwords()

itchatmp.run(port = 6490)
