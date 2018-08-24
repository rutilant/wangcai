from tinydb import TinyDB, Query

rule_table = TinyDB('rule_table.json')
history = TinyDB('history.json')
pointboard =TinyDB('pointboard.json')

history.purge()
pointboard.purge()
rule_table.purge()
rule_table.insert_multiple([{'event':'铲屎','point':3,'category':'猫务','note':''},
                            {'event':'喂化毛膏', 'point':1,'category':'猫务','note':''},
                            {'event':'梳毛','point':3,'category':'猫务','note':''},
                            {'event':'洗猫碗','point':2,'category':'猫务','note':''},
                            {'event':'加猫粮', 'point':1,'category':'猫务','note':''},
                            {'event':'加猫水','point':2,'category':'猫务','note':''},
                            {'event':'剪指甲','point':4,'category':'猫务','note':''},
                            {'event':'吸床', 'point':3,'category':'家务','note':''},
                            {'event':'拖地','point':3,'category':'家务','note':''},
                            {'event':'洗衣服', 'point':3,'category':'家务','note':''},
                            {'event':'烘干衣服', 'point':2,'category':'家务','note':''},
                            {'event':'收碗','point':5,'category':'家务','note':''},
                            {'event':'收快递', 'point':2,'category':'家务','note':''},
                            {'event':'倒垃圾', 'point':1,'category':'家务','note':''},
                            {'event':'扫吸地','point':2,'category':'家务','note':'包括捡头发'},
                            {'event':'清理尘盒', 'point':2,'category':'家务','note':''},
                            {'event':'做方便食品', 'point':3,'category':'家务','note':'以煮泡面为标准'}])

# pointboard.insert({'userid':'','username':'','current_points':'','recent_change':'','user_chat_id':'','subscribe':'false'})