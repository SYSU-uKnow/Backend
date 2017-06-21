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
