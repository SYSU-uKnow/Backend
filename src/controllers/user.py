# -*- coding: utf-8 -*-
import os
import hashlib
import MySQLdb
import question
import functools
from flask import Blueprint, g, jsonify, request, session

user = Blueprint('user', __name__)

def check_session(fun):
  @functools.wraps(fun)
  def wrapper(*args, **kw):
    print("check session")
    if 'user_id' not in session:  # 未登录
      return jsonify({'status':403, 'errmsg':'未登录'})
    return fun(*args, **kw)
  return wrapper

def avatarMD5(avatar):
  MD5 = hashlib.md5()
  MD5.update(avatar)
  return MD5.hexdigest()

# 微信登录后完善信息
@user.route('/api/users/<int:user_id>/perfect', methods=['PATCH'])
@check_session
def perfectInfo(user_id):
  school = request.form.get("school")
  major = request.form.get("major")
  grade = request.form.get("grade")
  status = "%s%s%s" % (school, major, grade)
  avatarUrl = "%d.jpg" % user_id
  hasFile = True
  avatarmd5 = ""
  try:
    srcFile = request.files["avatar"]
  except:
    hasFile = False
  if hasFile:
    # 文件命名为user_id+后缀
    avatarUrl = str(user_id) + os.path.splitext(srcFile.filename)[1]
    srcFile.save("static/avatar/" + avatarUrl)
    avatarmd5 = avatarMD5(open("static/avatar/" + avatarUrl, "rb").read())

  ##返回的数据data
  data = {}
  data["status"]=200
  data["data"] = {}
  try:
    sql = """update user set avatarUrl='%s',status='%s',
       school='%s',major='%s',grade='%s', isNew=0
       where id=%d""" % (avatarUrl,status,school,major,grade,user_id)
    c = g.db.cursor()
    c.execute(sql)
    g.db.commit()
    data["data"]["md5"] = avatarmd5
  except Exception as e:
    print e
    data["errmsg"] = "完善信息失败"
    data["status"] = 500

  return jsonify(data)

# 3.点击头像跳转到提问页面
@user.route('/api/users/<int:user_id>/introduction')
@check_session
def introduction(user_id):
  id = request.args.get("id")
  c = g.db.cursor() 
  
  data = {}
  data["status"] = 200
  data["data"] = {}

  sql = '''select u.avatarUrl, u.username, u.description, u.status 
     from user u where u.id = %d''' % user_id
  c.execute(sql)
  result = c.fetchone()
  data["data"]["avatarUrl"] = result[0]
  data["data"]["username"] = result[1]
  data["data"]["description"] = result[2]
  data["data"]["status"] = result[3]

  #关注信息
  sql = '''select f.uid from follow f where followed_uid = %d''' % user_id
  c.execute(sql)
  results = c.fetchall()
  data["data"]["followedNum"] = len(results)
  data["data"]["followed"] = 0
  for row in results:
    if (row[0] == int(id)):
      data["data"]["followed"] = 1
      break

  #回答问题数
  sql = '''select count(*)
        from question q
        where q.answerer_id = %d''' % user_id
  c.execute(sql)
  ansNum = c.fetchone()
  data["data"]["ansNum"] = ansNum[0]

  #回答的问题
  data["data"]["answers"] = []
  sql = '''select q.id, q.description, q.answerer_id, q.audioSeconds
          from question q
          where q.answerer_id = %d and q.audioSeconds is not null''' % user_id
  c.execute(sql)
  results = c.fetchall()
  for row in results:
    record = {'id':row[0], 'description':row[1], 'audioSeconds':row[3]}
    tmp = question._getSomeDetail(row[0], row[2])
    record.update(tmp)
    data["data"]["answers"].append(record)

  return jsonify(data)

