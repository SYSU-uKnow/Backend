# -*- coding: utf-8 -*-
import os
import datetime
import MySQLdb
import functools
import jieba
from flask import Blueprint, g, jsonify, request, session

question = Blueprint('question', __name__)

def check_session(fun):
  @functools.wraps(fun)
  def wrapper(*args, **kw):
    if 'user_id' not in session:  # 未登录
      return jsonify({'status':403, 'errmsg':'未登录'})
    return fun(*args, **kw)
  return wrapper

def _getSomeDetail(question_id, answerer_id):
  c = g.db.cursor()
  tmp = {}
  if answerer_id:
    sql = '''select u.username, u.avatarUrl, u.status, u.description
           from user u where u.id = %d''' % answerer_id
    c.execute(sql)
    result = c.fetchone()
    tmp['answerer_username'] = result[0]
    tmp['answerer_avatarUrl'] = result[1]
    tmp['answerer_status'] = result[2]
    tmp['answerer_description'] = result[3]
  else:
    tmp['answerer_username'] = None
    tmp['answerer_avatarUrl'] = None
    tmp['answerer_status'] = None
    tmp['answerer_description'] = None

  #收听人数
  sql = 'select count(*) from listening l where l.qid = %d' % question_id
  c.execute(sql)
  listeningNum = c.fetchone()[0]
  
  #点赞人数
  sql = '''select count(*) from comment c where c.qid = %d and c.liked = 1''' % question_id
  c.execute(sql)
  praiseNum = c.fetchone()[0]

  tmp['listeningNum'] = listeningNum
  tmp['praiseNum'] = praiseNum

  return tmp

# 1. 推荐页面
@question.route('/api/questions/recommend')
@check_session
def getRecommend():
  c = g.db.cursor()
  data = {}
  data["status"] = 200

  id = session['user_id']

  sql = '''select u.status from user u where u.id=%s''' % id
  c.execute(sql)
  result = c.fetchone()
  status = result[0]

  # 分词
  query_statement = " ".join(jieba.cut(status))
  list = query_statement.split()

  count = 0
  data["data"] = []
  for string in list:
    sql = """select q.id, q.description, q.answerer_id, q.audioSeconds
          from question q where q.audioUrl is not null and q.description like \'%%%s%%\'""" % string
    c.execute(sql)
    results = c.fetchall()
    for row in results:
      record = {'id':row[0], 'description':row[1], 'answerer_id': row[2], 'audioSeconds':row[3]}
      tmp = _getSomeDetail(row[0], row[2])
      record.update(tmp)
      data["data"].append(record)
      count = count+1

  if count < 20:
    sql = """select q.id, q.description, q.answerer_id, q.audioSeconds
          from question q where q.audioUrl is not null"""
    c.execute(sql)
    results = c.fetchall()
    for row in results:
      record = {'id':row[0], 'description':row[1], 'answerer_id': row[2], 'audioSeconds':row[3]}
      tmp = _getSomeDetail(row[0], row[2])
      record.update(tmp)
      data["data"].append(record)
      count = count+1
      if count > 20:
        break

  return jsonify(data)


# 2. 点击问题后进入详情页面
@question.route('/api/questions/<int:question_id>')
@check_session
def questionDetail(question_id):
  c = g.db.cursor() 

  data = {}
  data["status"] = 200

  data["data"] = {}
  sql = '''select q.description, q.askDate, q.audioUrl, q.asker_id, q.answerer_id, q.audioSeconds
        from question q where q.id = %d''' % question_id

  c.execute(sql)
  result = c.fetchone()
  data['data']['id'] = question_id
  data['data']['description'] = result[0]
  data['data']['askDate'] = str(result[1])
  data['data']['audioUrl'] = result[2]
  data['data']['audioSeconds'] = result[5] 

  asker_id = result[3]
  answerer_id = result[4]

  sql = '''select u.username, u.avatarUrl from user u where u.id = %d''' % asker_id
  c.execute(sql)
  result = c.fetchone()
  data['data']['asker_username'] = result[0]
  data['data']['asker_avatarUrl'] = result[1]
  tmp = _getSomeDetail(question_id, answerer_id)
  data['data'].update(tmp)

  try:
    sql = '''select * from comment c where c.uid = %d and c.qid = %d''' % (int(session['user_id']), question_id)
    c.execute(sql)
    result = c.fetchone()
    if result == None:
      data['data']['commented'] = 0
    else:
      data['data']['commented'] = 1
      data['data']['liked'] = result[2]

  except Exception as e:
    del data['data']
    data["errmsg"] = "未评价"
    data["status"] = 500

  return jsonify(data)