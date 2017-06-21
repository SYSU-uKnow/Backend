# -*- coding: utf-8 -*-
import os
import MySQLdb
import question
import jieba
from flask import Blueprint, g, jsonify, request

visitor = Blueprint('visitor', __name__)

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