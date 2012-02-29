#!/usr/bin/env python
#-*- coding:utf-8 -*-
import db
import datetime

def scores():
    """
    获取游戏历史分数
    """
    d = datetime.date.today()
    today = datetime.datetime(d.year, d.month, d.day)
    dailys =  list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today, )))
    weeklys = list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today - datetime.timedelta(days=7), )))
    monthlys = list(db.cursor.execute('select * from (select name, count(*) as count from scores where time > ? group by name) order by count desc limit 10', (today - datetime.timedelta(days=30), )))
    return dict(dailys=dailys, weeklys=weeklys, monthlys=monthlys)
    
def add_score(game_time, winner_name):
    """
    追加一个比赛的结果到数据集中，保存winner的名字
    """
    db.cursor.execute('insert into scores values(?, ?)', (game_time, winner_name))
    db.db.commit()

        
