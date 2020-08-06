from hashlib import sha1 as _sha1
from tables import db, users, UsersInfo, Rating, Follow, ItemTeam, CV, Teammates, ProjectTheme, Chat, Message, \
    BlackList, Share
from flask import request
from datetime import datetime, date, timedelta
import logging
import json
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

_secret_key = 'secret'  # 计算token用


#
#
def DoFollow():
    """
    执行关注操作
    :return: 成功返回None,失败返回错误信息(状态码，描述)
    """
    try:
        token = request.form['token']
        befollowed = request.form['followee']
        the_type = request.form['type']
    except Exception as e:
        return 400, "服务器解析数据错误::%s" % e

    uid = identify(token)
    if uid:
        if the_type == "begin":
            try:
                temp = Follow.query.filter(Follow.follower == uid, Follow.befollowed == int(befollowed)).first()
                if temp is not None:
                    return 400, "已经关注过了"

                the_followee = UsersInfo.query.filter(UsersInfo.uid == int(befollowed)).first()
                new_record = Follow(follower=uid,
                                    befollowed=the_followee.uid,
                                    avatar=the_followee.avatar,
                                    nickname=the_followee.nickname)
            except Exception as e:
                return 500, "服务器创建对象时出错::%s" % e

            try:
                db.session.add(new_record)
                db.session.commit()
            except Exception as e:
                return 500, "关注，服务器数据库操作时出错::%s" % e
            return None
        else:
            try:
                the_record = Follow.query.filter(Follow.befollowed == int(befollowed), Follow.follower == uid).first()
                db.session.delete(the_record)
                db.session.commit()
            except Exception as e:
                return 500, "取消关注，服务器数据库操作时出错::%s" % e
            return None

    else:
        return 400, "token鉴别失败"


def DoShare():
    """
    发布分享
    :return: 成功返回(字典,None),失败返回(None,错误信息(错误码,描述信息))
    """
    try:
        data = json.loads(request.get_data(as_text=True))
    except Exception as e:
        return None, (500, "data=json.loads(request.get_data(as_text=True))错误::%s::data:" % e)
    try:
        token = data['publisherToken']
        uid = identify(token)
        brief = data['brief']
        content = data['content']
        category = ';'.join(data['categoty'])
    except Exception as e:
        return None, (500, "解析数据失败::%s" % e)

    if uid:
        try:
            new_share = Share(uid=uid,
                              brief=brief,
                              content=content,
                              category=category,
                              time=datetime.now())
            db.session.add(new_share)
            db.session.commit()
            the_id = new_share.id
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
        dic = {"status": 200, "msg": 'ok', "data": {"id": the_id}}
        return dic, None
    else:
        return None, (400, "token错误")


def DoProjectTheme():
    """
    发布项目主题
    :return: 成功返回(字典,None),失败返回(None,错误信息(错误码,描述信息))
    """
    data = request.form
    try:
        token = data['publisherToken']
        uid = identify(token)
    except Exception as e:
        return None, (400, "解析token出现错误::%s" % e)

    if uid:
        try:
            master = UsersInfo.query.filter(UsersInfo.uid == uid).first()

            dic = {"status": 200, "msg": 'ok'}
            new = ProjectTheme(publisher_id=uid,
                               publisherName=master.nickname,
                               publisherAvatar=master.avatar,
                               brief=data['brief'],
                               content=data['content'],
                               cover=data['cover']
                               )
            db.session.add(new)
            db.session.commit()
            dic['data'] = {"id": new.id}
            return dic, None
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
    else:
        return None, (400, "token错误")


def DoProjectTeam():
    """
    发布组队
    :return: 成功返回(字典,None),失败返回(None,错误信息(错误码,描述))
    """
    try:
        data = json.loads(request.get_data(as_text=True))
    except Exception as e:
        return None, (500, "data=json.loads(request.get_data(as_text=True))错误::%s::data:" % e)

    try:
        token = data['token']
    except Exception as e:
        return None, (500, "token=data['token']错误")

    try:
        uid = identify(token)
    except Exception as e:
        return None, (500, "服务器鉴别token失败::%s" % e)

    if uid:
        try:
            types = data['type']
            majors = data['major']
            begin_date = datetime.strptime(data['beginDate'], '%Y/%m/%d').date()
            new_team = ItemTeam(master_id=uid,
                                title=data['title'],
                                types=';'.join(types),
                                begin_date=begin_date,
                                rank=data['rank'],
                                describe=data['description'],
                                period=data['period'],
                                publishTime=datetime.now(),
                                req_num=data['memberNum'],
                                req_mate_grade=data['grade'],
                                req_technique=data['skill'],
                                req_major=';'.join(majors),
                                finished=False,
                                )
        except Exception as e:
            # return None, (501, "服务器解析数据/创建对象出错::%s" % e)
            return None, (501, "服务器收到数据data=" + str(data))
        try:
            db.session.add(new_team)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return None, (500, "服务器数据库提交出错::%s" % e)

        try:
            first_mate = Teammates(item_id=new_team.id, uid=uid)
            db.session.add(first_mate)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.delete(new_team)
            db.session.commit()
            return None, (500, "!!将master加入队伍（初始）失败,项目创建失败::%s" % e)

        return {"status": 200, "msg": 'ok', "data": {"id": new_team.id}}, None
    else:
        return None, (400, "token错误")


def DoRate():
    """
    进行评分
    :return: 成功返回None,失败返回错误信息(错误码，描述)
    """
    data = request.form
    try:
        token = data['token']
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token出错::%s" % e

    if uid:
        try:
            is_rated = Rating.query.filter(Rating.uid1 == uid, Rating.uid2 == data['ratee']).first()
            if is_rated:
                return 400, "已评价过了"

            new_rate = Rating(uid1=uid,
                              uid2=data['ratee'],
                              attitude=data['attitude'],
                              capability=data['capability'],
                              personality=data['personality'],
                              describe=data['description'],
                              datetime=datetime.now(),
                              isChecked=False)
        except Exception as e:
            return 500, "提交表单错误/服务器创建对象出错%s" % e

        try:
            the_user = UsersInfo.query.filter(UsersInfo.uid == uid).first()
            if data['rater'] != '':
                # 不是匿名
                new_rate.nickname = the_user.nickname
                new_rate.avatar = the_user.avatar
            else:
                new_rate.nickname = None
                new_rate.avatar = None

            db.session.add(new_rate)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库操作出错 %s" % e

        return None
    else:
        return 400, "token错误"


def DoRegister():
    """
    进行注册
    :return: 成功返回None,失败返回错误信息(错误码，描述)
    """
    data = request.form
    try:
        new_user = users(name=data['userID'],
                         passwd=data['password'])

        new_user_info = UsersInfo(avatar=data['avatar'],
                                  nickname=data['nickname'],
                                  gender=data['gender'],
                                  description=data['description'],
                                  school=data['school'],
                                  schoolID=data['schoolID'],
                                  major=data['major'],
                                  grade=data['grade'],
                                  interest=data['interest'])
        data = str(data)
    except Exception as e:
        return 400, str(data)

    t = users.query.filter(users.name == new_user.name).first()
    if t:
        return 400, "用户名已注册"

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return 500, "服务器数据库故障::%s" % e

    try:
        new_user_info.uid = new_user.id
        db.session.add(new_user_info)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        db.session.delete(new_user)
        db.session.commit()
        return 500, "服务器数据库故障::%s" % e

    return None


def DoLogin():
    """
    登录
    :return: 成功返回(字典，None),失败返回(None,错误信息(错误码，描述))
    """
    try:
        username = request.form['userID']
        password = request.form['password']
    except KeyError as e:
        return None, (400, "服务器解析form出现KeyError")
    token, uid = CheckPassword(username, password)
    if token:
        return {"status": 200, "msg": 'ok', "data": {"token": token, "userID": uid}}, None
    else:
        return None, (400, "密码错误/用户名不存在")


def DoResume():
    """
    增加简历
    :return:成功返回None,失败返回错误信息(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败::%s" % e

    if uid:
        try:
            new_resume = CV(uid=uid,
                            resume=request.form['resume'])
        except Exception as e:
            return 500, "服务器创建对象失败::%s" % e

        try:
            db.session.add(new_resume)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库提交失败::%s" % e

        return None

    else:
        return 400, "token错误"


def DoChat():
    """
    发私信
    :return: 成功返回None,失败返回(错误码,描述信息)
    """
    data = request.form
    try:
        token = data['token']
        uid = identify(token)
    except Exception as e:
        return 400, "获得token/鉴别token出错::%s" % e
    if uid:
        try:
            from_user = UsersInfo.query.filter(UsersInfo.uid == uid).first()
            new_chat = Chat(from_uid=uid,
                            fromAvatar=from_user.avatar if data['from'] != '' else None,
                            fromName=from_user.nickname if data['from'] != '' else None,
                            to_uid=data['to'],
                            message=data['message'],
                            time=datetime.now()
                            )
            db.session.add(new_chat)
            db.session.commit()
        except Exception as e:
            return 500, "服务器错误::%s" % e
        return None
    else:
        return 400, "token错误"


def DoJoin():
    """
    申请加入队伍
    :return: 成功None,失败(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
    except Exception as e:
        return 500, "无法解析token::%s" % e
    if uid:
        try:
            the_project = ItemTeam.query.filter(ItemTeam.id == request.form['target'],
                                                False == ItemTeam.finished).first()
            if the_project is None:
                return 400, "查询不到该项目/项目已经结束::%s" % str(request.form['target'])

            temp = Message.query.filter(Message.from_uid == uid,
                                        Message.project_id == the_project.id, None == Message.response).first()
            if temp is not None:
                return 400, "已发送过申请了,请等待回应"

            temp = Teammates.query.filter(Teammates.uid == uid, Teammates.item_id == the_project.id).first()
            if temp is not None:
                return 400, "已在队伍中"

            new_msg = Message(from_uid=uid,
                              project_id=the_project.id,
                              project_title=the_project.title,
                              master_id=the_project.master_id,
                              message=request.form['message'],
                              time=datetime.now(),
                              isCheck_request=False,
                              isCheck_response=False
                              )
            db.session.add(new_msg)
            db.session.commit()
        except Exception as e:
            return 500, "服务器错误::%s" % e
        return None
    else:
        return 400, "token错误"


def DoResponseJoin():
    """
    回应组队消息
    :return: 成功返回None,失败返回(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败::%s" % e

    if uid:
        try:
            accepted = request.form['accepted']
            target = request.form['target']
            from_id = request.form['from']
            response = request.form['message']
            the_req = Message.query.filter(Message.project_id == target, Message.from_uid == from_id,
                                           None == Message.response).first()

            if the_req is None:
                return 400, "错误/查询不到该条记录/已经回应了"

            if uid != the_req.master_id:
                return 400, "不是该项目的发布者，权限不足"

            # 更改请求的状态
            the_req.state = True if accepted == 'true' else False
            the_req.response = response

            temp = Teammates.query.filter(Teammates.uid == from_id, Teammates.item_id == target).first()
            if temp is not None:
                return 400, "已经同意过了"

            # 同意加入队伍
            if the_req.state:
                new_mate = Teammates(uid=from_id, item_id=target)
                db.session.add(new_mate)
            db.session.add(the_req)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return 500, "服务器错误::%s" % e
        return None
    else:
        return 400, "token错误"


def DoFinishProject():
    """
    结束项目
    :return: 成功:None,失败:(错误码,描述信息)
    """
    try:
        token = request.form['token']
        project_id = request.form['id']
        uid = identify(token)
    except Exception as e:
        return 400, "获取数据失败::%s" % e

    if uid:
        try:
            the_project = ItemTeam.query.filter(ItemTeam.id == project_id, ItemTeam.master_id == uid).first()
            if the_project is None:
                return 400, "错误，不是这个项目的发起者"
            else:
                the_project.finished = True
                db.session.add(the_project)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            return 500, "获取数据失败::%s" % e
    else:
        return 400, "token错误"


def DoReject():
    """
    拉黑/解除拉黑
    :return: 成功:None,失败:(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
        the_type = request.form['type']
    except Exception as e:
        return 400, "服务器无法解析token/the_type::%s" % e

    if uid:
        try:
            temp = BlackList.query.filter(BlackList.rejecter == uid,
                                          BlackList.berejecter == request.form['rejectee']
                                          ).first()
            if the_type == 'reject':
                if temp is not None:
                    return 400, "已拉黑"

                new_record = BlackList(rejecter=uid,
                                       berejecter=request.form['rejectee'])
                db.session.add(new_record)
                db.session.commit()
            else:
                if temp is None:
                    return 400, "对方不在黑名单中，无法进行解除操作"
                db.session.delete(temp)
                db.session.commit()

        except Exception as e:
            db.session.rollback()
            return 500, "服务器错误::%s" % e
        return None
    else:
        return 400, "token错误"


def DoCheck():
    """
    标记信息为已读
    :return: 成功:None,失败:(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
        target = request.form['target']
        the_type = request.form['type']
        isChecked = request.form['isChecked']
    except Exception as e:
        return 400, "服务器获取数据失败::%s" % e

    if uid:
        try:
            modify_record = None
            if the_type == 'rate':
                modify_record = Rating.query.filter(Rating.id == target).first()
                modify_record.isChecked = True if isChecked == 'true' else False
            elif the_type == 'request':
                modify_record = Message.query.filter(Message.id == target).first()
                modify_record.isCheck_request = True if isChecked == 'true' else False
            elif the_type == 'response':
                modify_record = Message.query.filter(Message.id == target).first()
                modify_record.isCheck_response = True if isChecked == 'true' else False
            elif the_type == 'message':
                modify_record = Chat.query.filter(Chat.id == target).first()
                modify_record.isChecked = True if isChecked == 'true' else False

            db.session.add(modify_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return 500, "服务器错误::%s" % e
        return None
    else:
        return 400, "token错误"


def DoUpload(the_type):
    """
    上传图片
    :return: 成功(字典,None),失败(None,(错误码,描述信息))
    """
    try:
        f = request.files['file']
    except Exception as e:
        return None, (400, "无法获取file")

    try:
        extension = f.filename.split('.')[-1]
        path = './static/' + the_type + '/' + sha1(str(datetime.now())) + '.' + extension
        f.save(path)
    except Exception as e:
        return None, (500, "服务器保存文件错误%s" % e)

    return {"status": 200, "msg": 'ok', "data": {"url": path[1:]}}, None


def GetUserInfo():
    """
    获取用户信息的字典
    :return: 成功返回(字典，None),失败返回(None,错误信息(错误码，描述))
    """
    uids = request.args.getlist('userID')
    if uids is None:
        return None, (400, "获取userID失败")
    dic = {"status": 200, "msg": 'ok'}
    data = []
    for uid in uids:
        obj = UsersInfo.query.filter(UsersInfo.uid == int(uid)).first()
        if not obj:
            return None, (500, "找不到uid=%d的用户" % int(uid))
        else:
            # 基本信息
            the_data = {"avatar": obj.avatar,
                        "nickname": obj.nickname,
                        "gender": obj.gender,
                        "description": obj.description,
                        "school": obj.school,
                        "schoolID": obj.schoolID,
                        "major": obj.major,
                        "grade": obj.grade,
                        "interest": obj.interest}

            # 关注与被关注
            follows = Follow.query.filter(Follow.follower == uid).count()
            befollowed = Follow.query.filter(Follow.befollowed == uid).count()
            the_data['followingNum'] = follows
            the_data['followerNum'] = befollowed

            # 评分
            grade = [0, 0, 0]
            all_rate = Rating.query.filter(Rating.uid2 == obj.uid).all()
            for i in all_rate:
                grade[0] += i.attitude
                grade[1] += i.capability
                grade[2] += i.personality
            rating = {"ratedNum": len(all_rate),
                      "attitude": grade[0],
                      "capability": grade[1],
                      "personality": grade[2]}
            the_data["rating"] = rating

            data.append(the_data)
    dic['data'] = data
    return dic, None


def GetRate():
    """
    获取评分
    :return: 成功返回(list，None),失败返回(None,错误信息(错误码，描述))
    """
    uid = request.args.get('userID')
    if uid is None:
        return None, (400, "获取userID失败")
    result = Rating.query.filter(Rating.uid2 == int(uid)).order_by(Rating.id.desc()).all()
    dic = {"status": 200, "msg": 'ok'}
    all_rate = []

    all_black = BlackList.query.filter(BlackList.rejecter == uid).all()
    black = []
    for i in all_black:
        black.append(i.berejecter)

    for i in result:
        if i.uid1 in black:
            continue
        all_rate.append({"rater": None if i.avatar is None else i.uid1,
                         "raterName": i.nickname,
                         "ratee": i.uid2,
                         "attitude": i.attitude,
                         "raterAvatar": i.avatar,
                         "capability": i.capability,
                         "personality": i.personality,
                         "description": i.describe,
                         "time": i.datetime.timestamp(),
                         "id": i.id,
                         "isChecked": i.isChecked})
    dic['data'] = all_rate
    return dic, None


def GetFollows():
    """
    获得所有关注者
    :return: 成功:(字典，None),失败(None,错误信息(状态码，描述))
    """
    uid = request.args.get('userID')
    if uid is None:
        return None, (400, "获取userID失败")

    all_follows = Follow.query.filter(Follow.follower == int(uid))
    dic = {"status": 200, "msg": 'ok'}
    data = []
    for i in all_follows:
        the_follower = UsersInfo.query.filter(UsersInfo.uid == i.befollowed).first()
        data.append({"userID": the_follower.uid,
                     "avatar": the_follower.avatar,
                     "nickname": the_follower.nickname,
                     "description": the_follower.description})
    dic['data'] = data
    return dic, None


def GetFollowers():
    """
    获得所有粉丝
    :return: 成功:(字典，None),失败(None,错误信息(状态码，描述))
    """
    uid = request.args.get('userID')
    if uid is None:
        return None, (400, "获取userID失败")

    all_follows = Follow.query.filter(Follow.befollowed == int(uid))
    dic = {"status": 200, "msg": 'ok'}
    data = []
    for i in all_follows:
        the_befollowed = UsersInfo.query.filter(UsersInfo.uid == i.follower).first()
        data.append({"userID": the_befollowed.uid,
                     "avatar": the_befollowed.avatar,
                     "nickname": the_befollowed.nickname,
                     "description": the_befollowed.description})
    dic['data'] = data
    return dic, None


def GetShare():
    """
    获得分享
    :return: 成功:(字典，None),失败(None,错误信息(状态码，描述))
    """
    the_id = request.args.get('id')
    if the_id is None:
        return None, (400, "获取id失败")
    dic = {"status": 200, "msg": 'ok'}
    if the_id == 'all':
        try:
            data = []
            all_shares = Share.query.order_by(Share.time.desc()).all()
            for i in all_shares:
                publisher = UsersInfo.query.filter(UsersInfo.uid == i.uid).first()
                data.append({"id": i.id,
                             "publisher": publisher.uid,
                             "publisherName": publisher.nickname,
                             "publisherAvatar": publisher.avatar,
                             "brief": i.brief,
                             "categoty": i.category,
                             "time": i.time.timestamp()})
            dic['data'] = data
            return dic, None
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
    else:
        try:
            the_share = Share.query.filter(Share.id == int(the_id)).first()
            publisher = UsersInfo.query.filter(UsersInfo.uid == the_share.uid).first()
            data = {"id": the_share.id,
                    "publisher": publisher.uid,
                    "publisherName": publisher.nickname,
                    "publisherAvatar": publisher.avatar,
                    "brief": the_share.brief,
                    "content": the_share.content,
                    "categoty": the_share.category,
                    "time": the_share.time.timestamp()}
            dic['data'] = data
            return dic, None
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)


def GetUserShares():
    """
    获得用户所有分享
    :return: 成功:(字典，None),失败(None,错误信息(状态码，描述))
    """
    the_id = request.args.get('userID')
    if the_id is None:
        return None, (400, "获取id失败")
    dic = {"status": 200, "msg": 'ok'}
    try:
        data = []
        all_shares = Share.query.filter(Share.uid == the_id).order_by(Share.time.desc()).all()
        publisher = UsersInfo.query.filter(UsersInfo.uid == the_id).first()
        for i in all_shares:
            data.append({"id": i.id,
                         "publisher": publisher.uid,
                         "publisherName": publisher.nickname,
                         "publisherAvatar": publisher.avatar,
                         "brief": i.brief,
                         "categoty": i.category,
                         "time": i.time.timestamp()})
        dic['data'] = data
        return dic, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetProject():
    """
    获取发布内容
    :return: 成功:(json数据,None),失败:(None,错误信息(状态码,描述信息))
    """
    pid = request.args.get('id')
    keyword = request.args.get('keyword')
    if pid is None and keyword is None:
        return None, (400, "无法获取id值/keyword值")

    dic = {"status": 200, "msg": 'ok'}

    if keyword:
        try:
            result = ItemTeam.query.all()
            data = []
            for i in reversed(result):
                if related(keyword, i):
                    types = i.types.split(';')
                    majors = i.req_major.split(';')
                    begin_date = str(i.begin_date).replace('-', '/')

                    data.append({"id": i.id,
                                 "finished": i.finished,
                                 "title": i.title,
                                 "type": types,
                                 "rank": i.rank,
                                 "major": majors,
                                 "period": i.period,
                                 "beginDate": begin_date,
                                 "memberNum": i.req_num,
                                 })
            dic['data'] = data
            return json.dumps(dic), None
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)

    if pid == 'all':
        try:
            cache = r.get('project::all')
            if cache is None:
                result = ItemTeam.query.all()
                data = []
                for i in reversed(result):
                    types = i.types.split(';')
                    majors = i.req_major.split(';')
                    begin_date = str(i.begin_date).replace('-', '/')

                    user_in_team = Teammates.query.filter(Teammates.item_id == i.id).all()
                    members = []
                    for j in user_in_team:
                        members.append(j.uid)

                    data.append({"id": i.id,
                                 "finished": i.finished,
                                 "title": i.title,
                                 "type": types,
                                 "rank": i.rank,
                                 "major": majors,
                                 "period": i.period,
                                 "beginDate": begin_date,
                                 "memberNum": i.req_num,
                                 "members": members
                                 })
                dic['data'] = data
                final_data = json.dumps(dic)
                r.set('project::all', final_data, ex=5)
                return final_data, None
            else:
                return cache, None

        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
    else:
        try:
            the_user_id = request.args.get('userID')
            if the_user_id is not None:
                # 历史记录
                r.lpush('history::' + str(the_user_id), int(pid))
                r.ltrim('history::' + str(the_user_id), 0, 999)

            cache = r.get('project::' + pid)
            if cache is None:
                the_project = ItemTeam.query.filter(ItemTeam.id == int(pid)).first()

                if the_project is None:
                    return None, (400, "查询不到该项目")

                master = UsersInfo.query.filter(UsersInfo.uid == the_project.master_id).first()

                types = the_project.types.split(';')
                majors = the_project.req_major.split(';')
                begin_date = str(the_project.begin_date).replace('-', '/')

                user_in_team = Teammates.query.filter(Teammates.item_id == the_project.id).all()
                members = []
                for j in user_in_team:
                    members.append(j.uid)

                data = {"id": the_project.id,
                        "finished": the_project.finished,
                        "publisher": master.uid,
                        "publisherAvatar": master.avatar,
                        "publisherName": master.nickname,
                        "publishTime": the_project.publishTime.timestamp(),
                        "title": the_project.title,
                        "type": types,
                        "rank": the_project.rank,
                        "major": majors,
                        "period": the_project.period,
                        "beginDate": begin_date,
                        "description": the_project.describe,
                        "memberNum": the_project.req_num,
                        "grade": the_project.req_mate_grade,
                        "skill": the_project.req_technique,
                        "members": members,
                        }
                dic['data'] = data
                final_data = json.dumps(dic)
                r.set('project::' + str(pid), final_data, ex=5)
                return final_data, None
            else:
                return cache, None

        except Exception as e:
            return None, (500, "服务器错误::%s" % e)


def GetResume():
    """
    获取简历
    :return:成功返回(字典数据,None),失败返回(None,错误信息(错误码,描述信息))
    """
    try:
        uid = int(request.args.get('userID'))
    except Exception as e:
        return None, (400, "获取userID失败::%s" % e)

    try:
        result = CV.query.filter(CV.uid == uid).first()
    except Exception as e:
        return None, (500, "服务器查询错误::%s" % e)

    if result is None:
        return None, (400, "无该用户简历")

    try:
        dic = {"status": 200, "msg": 'ok', "data": {"resume": result.resume}}
        return dic, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetChat():
    """
    获得私信
    :return: 成功返回(字典,None),失败返回(None,错误信息(错误码,描述信息))
    """
    uid = request.args.get('userID')
    if uid is None:
        return None, (400, "无法获取uid")

    try:
        all_chat = Chat.query.filter(Chat.to_uid == uid).order_by(Chat.time.desc()).all()
        dic = {"status": 200, "msg": 'ok'}
        data = []

        all_black = BlackList.query.filter(BlackList.rejecter == uid).all()
        black = []
        for i in all_black:
            black.append(i.berejecter)

        for i in all_chat:
            if i.from_uid in black:
                continue

            data.append({"from": i.from_uid if i.fromName is not None else None,
                         "fromName": i.fromName,
                         "fromAvatar": i.fromAvatar,
                         "to": uid,
                         "message": i.message,
                         "time": i.time.timestamp(),
                         "id": i.id,
                         "isChecked": i.isChecked
                         })
        dic['data'] = data
        return dic, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetJoin():
    """
    获取申请加入的信息
    :return: 成功:(字典,None),失败:(None,(错误码,错误信息))
    """
    try:
        token = request.args.get('token')
        uid = identify(token)
    except Exception as e:
        return None, (500, "服务器无法解析token::%s" % e)

    if uid:
        try:
            dic = {"status": 200, "msg": 'ok'}
            data = []
            all_msg = Message.query.filter(Message.master_id == uid, None == Message.state).all()
            all_black = BlackList.query.filter(BlackList.rejecter == uid).all()
            black = []
            for i in all_black:
                black.append(i.berejecter)

            for i in reversed(all_msg):
                if i.from_uid in black:
                    continue
                from_user = UsersInfo.query.filter(UsersInfo.uid == i.from_uid).first()
                data.append({"target": i.project_id,
                             "message": i.message,
                             "title": i.project_title,
                             "from": from_user.uid,
                             "fromAvatar": from_user.avatar,
                             "fromName": from_user.nickname,
                             "time": i.time.timestamp(),
                             "id": i.id,
                             "isChecked": i.isCheck_request
                             })
            dic['data'] = data
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
        return dic, None

    else:
        return None, (400, "token错误")


def GetBlack():
    """
    获取黑名单
    :return: 成功返回(字典,None),失败返回(None,(错误码,描述))
    """
    try:
        token = request.args.get('token')
        uid = identify(token)
    except Exception as e:
        return None, (400, "服务器解析token错误::%s" % e)

    if uid:
        try:
            all_black = BlackList.query.filter(BlackList.rejecter == uid).all()
            dic = {"status": 200, "msg": 'ok'}
            data = []
            for i in all_black:
                the_user = UsersInfo.query.filter(UsersInfo.uid == i.berejecter).first()
                data.append({"userID": the_user.id,
                             "avatar": the_user.avatar,
                             "nickname": the_user.nickname,
                             "description": the_user.description})
            dic['data'] = data
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
        return dic, None
    else:
        return None, (400, "token错误")


def GetResponseJoin():
    """
    获得得到响应的消息
    :return: 成功返回(字典,None),失败返回(None,(错误码,描述))
    """
    try:
        token = request.args.get('token')
        uid = identify(token)
    except Exception as e:
        return None, (400, "服务器解析form出现Error::%s" % e)

    if uid:
        try:
            all_req = Message.query.filter(Message.from_uid == uid, None != Message.response).all()
            dic = {"status": 200, "msg": 'ok'}
            data = []
            for i in reversed(all_req):
                data.append({"accepted": i.state,
                             "target": i.project_id,
                             "title": i.project_title,
                             "message": i.response,
                             "time": i.time.timestamp(),
                             "id": i.id,
                             "isChecked": i.isCheck_response
                             })
            dic['data'] = data
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
        return dic, None
    else:
        return None, (400, "token错误")


def GetHistoryProject():
    """
    获取用户参加过的所有项目
    :return: 成功(字典,None),失败(None,(错误码,错误信息))
    """
    uid = request.args.get('userID')
    if uid is None:
        return None, (400, "无法获得查询userID")

    try:
        all_record = Teammates.query.filter(Teammates.uid == uid).all()
        dic = {"status": 200, "msg": 'ok'}
        data = []
        for i in reversed(all_record):
            the_project = ItemTeam.query.filter(ItemTeam.id == i.item_id).first()

            types = the_project.types.split(';')
            majors = the_project.req_major.split(';')
            begin_date = str(the_project.begin_date).replace('-', '/')

            data.append({"id": the_project.id,
                         "title": the_project.title,
                         "finished": the_project.finished,
                         "type": types,
                         "rank": the_project.rank,
                         "major": majors,
                         "period": the_project.period,
                         "beginDate": begin_date,
                         "memberNum": the_project.req_num,
                         })
        dic['data'] = data
        return dic, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetSearchUsers():
    """
    搜索用户
    :return: 成功(字典,None),失败(None,(错误码,错误信息))
    """
    key = request.args.get('keyword')
    if key is None:
        return None, (400, "无法获得查询userID")
    try:
        all_record = UsersInfo.query.all()
        dic = {"status": 200, "msg": 'ok'}
        data = []
        for i in reversed(all_record):

            if key in i.nickname:
                data.append({"userID": i.id,
                             "avatar": i.avatar,
                             "nickname": i.nickname,
                             "description": i.description
                             })

        dic['data'] = data
        return dic, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetSearchShares():
    """
    搜索分享
    :return: 成功(字典,None),失败(None,(错误码,错误信息))
    """
    key = request.args.get('keyword')
    if key is None:
        return None, (400, "无法获得查询userID")
    try:
        dic = {"status": 200, "msg": 'ok'}
        data = []
        all_shares = Share.query.all()
        for i in reversed(all_shares):
            if key in i.brief or key in i.category:
                publisher = UsersInfo.query.filter(UsersInfo.uid == i.uid).first()
                data.append({"id": i.id,
                             "publisher": publisher.uid,
                             "publisherName": publisher.nickname,
                             "publisherAvatar": publisher.avatar,
                             "brief": i.brief,
                             "categoty": i.category,
                             "time": i.time.timestamp()})
        dic['data'] = data
        return dic, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetProjectTheme():
    """
    获取主题项目
    :return: 成功(数据,None),失败(None,(错误码,描述信息))
    """
    pid = request.args.get('id')
    limit = request.args.get('limit')
    sort = request.args.get('sort')
    if pid is None:
        return None, (400, "无法获取查询id值")
    dic = {"status": 200, "msg": 'ok'}
    try:
        if pid == 'all':
            if sort is None and limit is None:
                # 按时间获取全部
                cache = r.get('ProjectTheme::all')
                if cache is None:
                    data = []

                    all_theme = ProjectTheme.query.order_by(ProjectTheme.id.desc()).all()
                    for i in all_theme:
                        data.append({"id": i.id,
                                     "publisher": i.publisher_id,
                                     "publisherName": i.publisherName,
                                     "publisherAvatar": i.publisherAvatar,
                                     "brief": i.brief,
                                     "cover": i.cover})
                    dic['data'] = data
                    final_data = json.dumps(dic)
                    r.set('ProjectTheme::all', final_data, ex=5)
                    return final_data, None
                else:
                    return cache, None
            elif sort == 'hot':
                # 按点击量获取
                if limit is not None:
                    limit = -int(limit)
                else:
                    limit = -100
                cache = r.get('cache::click::theme')
                if cache is None:

                    click_data = r.hgetall('click::theme')
                    for i in click_data:
                        # redis返回数据的value转int
                        click_data[i] = int(click_data[i])

                    click_data = sorted(click_data.items(), key=lambda kv: (kv[1], kv[0]))[limit:]
                    data = []

                    for i in reversed(click_data):
                        the_theme = ProjectTheme.query.filter(ProjectTheme.id == int(i[0])).first()
                        data.append({"id": the_theme.id,
                                     "publisher": the_theme.publisher_id,
                                     "publisherName": the_theme.publisherName,
                                     "publisherAvatar": the_theme.publisherAvatar,
                                     "brief": the_theme.brief,
                                     "cover": the_theme.cover})

                    dic['data'] = data
                    final_data = json.dumps(dic)
                    r.set('cache::click::theme', final_data, ex=5)
                    return final_data, None
                else:
                    return cache, None
            else:
                # 带limit的all
                cache = r.get('ProjectTheme::all::'+limit)
                if cache is None:
                    data = []
                    all_theme = ProjectTheme.query.order_by(ProjectTheme.id.desc()).limit(int(limit)).all()
                    for i in all_theme:
                        data.append({"id": i.id,
                                     "publisher": i.publisher_id,
                                     "publisherName": i.publisherName,
                                     "publisherAvatar": i.publisherAvatar,
                                     "brief": i.brief,
                                     "cover": i.cover})
                    dic['data'] = data
                    final_data = json.dumps(dic)
                    r.set('ProjectTheme::all::'+limit, final_data, ex=5)
                    return final_data, None
                else:
                    return cache, None
        else:
            cache = r.get('ProjectTheme::' + str(pid))
            if cache is None:
                the_theme = ProjectTheme.query.filter(ProjectTheme.id == int(pid)).first()
                dic['data'] = {"id": the_theme.id,
                               "publisher": the_theme.publisher_id,
                               "publisherName": the_theme.publisherName,
                               "publisherAvatar": the_theme.publisherAvatar,
                               "brief": the_theme.brief,
                               "content": the_theme.content,
                               "cover": the_theme.cover}
                final_data = json.dumps(dic)
                r.set('ProjectTheme::' + str(pid), final_data, ex=5)
                r.hincrby('click::theme', str(pid), 1)
                return final_data, None
            else:
                r.hincrby('click::theme', str(pid), 1)
                return cache, None
    except Exception as e:
        return None, (500, "服务器错误::%s" % e)


def GetBrowseHistory():
    """
    获得浏览历史
    :return: 成功返回(字典,None),失败返回(None,(错误码,描述))
    """
    try:
        token = request.args.get('token')
        uid = identify(token)
    except Exception as e:
        return None, (400, "服务器解析form出现Error::%s" % e)

    if uid:
        try:
            history = r.lrange('history::' + str(uid), 0, -1)
            dic = {"status": 200, "msg": 'ok'}
            data = []
            if history is None:
                dic['data'] = history
                return dic, None

            the_history = []
            # 待
            for i in history:
                if i not in the_history:
                    the_history.append(i)

            for i in the_history:
                the_project = ItemTeam.query.filter(ItemTeam.id == int(i)).first()
                if the_project is None:
                    continue

                types = the_project.types.split(';')
                majors = the_project.req_major.split(';')
                begin_date = str(the_project.begin_date).replace('-', '/')

                user_in_team = Teammates.query.filter(Teammates.item_id == the_project.id).all()
                members = []
                for j in user_in_team:
                    members.append(j.uid)

                data.append({"id": the_project.id,
                             "finished": the_project.finished,
                             "title": the_project.title,
                             "type": types,
                             "rank": the_project.rank,
                             "major": majors,
                             "period": the_project.period,
                             "beginDate": begin_date,
                             "memberNum": the_project.req_num,
                             "members": members,
                             })
            dic['data'] = data
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
        return dic, None
    else:
        return None, (400, "token错误")


def GetCountNewMsg():
    """
    获得新消息数量
    :return: 成功返回(字典,None),失败返回(None,(错误码,描述))
    """
    try:
        token = request.args.get('token')
        uid = identify(token)
    except Exception as e:
        return None, (400, "服务器解析form出现Error::%s" % e)

    if uid:
        try:
            black = []
            all_black = BlackList.query.filter(BlackList.rejecter == uid).all()
            for i in all_black:
                black.append(i.berejecter)
            num = 0
            # 要考虑黑名单，不能更改已读未读防止解除拉黑，用不了count，这效率太低了/(ㄒoㄒ)/~~
            num1 = Rating.query.filter(Rating.uid2 == uid, Rating.isChecked == False, Rating.uid1.notin_(black)).count()

            num2 = Message.query.filter(Message.from_uid == uid, Message.isCheck_response == False,
                                        Message.master_id.notin_(black)).count()

            num3 = Message.query.filter(Message.master_id == uid, Message.isCheck_request == False,
                                        Message.from_uid.notin_(black)).count()

            num4 = Chat.query.filter(Chat.to_uid == uid, Chat.isChecked == False, Chat.from_uid.notin_(black)).count()

            dic = {"status": 200, "msg": 'ok', "data": {"number": num1 + num2 + num3 + num4}}
        except Exception as e:
            return None, (500, "服务器错误::%s" % e)
        return dic, None
    else:
        return None, (400, "token错误")


def ModifyResume():
    """
    修改简历
    :return:成功返回None,失败返回错误信息(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败::%s" % e

    if uid:
        try:
            the_resume = CV.query.filter(CV.uid == uid).first()
            the_resume.resume = request.form['resume']
        except Exception as e:
            return 500, "服务器创建对象失败::%s" % e

        try:
            db.session.add(the_resume)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库提交失败::%s" % e

        return None

    else:
        return 400, "token错误"


def ModifyInfo():
    """
    修改个人信息
    :return:成功返回None,失败返回错误信息(错误码,描述信息)
    """
    try:
        token = request.form['token']
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败::%s" % e

    if uid:
        try:
            the_user = UsersInfo.query.filter(UsersInfo.uid == uid).first()
            if the_user is None:
                return 400, "查询不到改用户"
            the_user.avatar = request.form['avatar']
            the_user.nickname = request.form['nickname']
            the_user.gender = request.form['gender']
            the_user.description = request.form['description']
            the_user.schoolID = request.form['schoolID']
            the_user.major = request.form['major']
            the_user.grade = request.form['grade']
        except Exception as e:
            return 500, "服务器创建对象失败::%s" % e

        try:
            db.session.add(the_user)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库提交失败::%s" % e

        return None

    else:
        return 400, "token错误"


def ModifyPassword():
    """
    修改密码
    :return:成功返回None,失败返回错误信息(错误码,描述信息)
    """
    try:
        token = request.form['token']
        passwd = request.form['password']
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败::%s" % e

    if uid:
        try:
            the_user = users.query.filter(users.id == uid).first()
            the_user.passwd = passwd
        except Exception as e:
            return 500, "服务器创建对象失败::%s" % e

        try:
            db.session.add(the_user)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库提交失败::%s" % e

        return None

    else:
        return 400, "token错误"


def DeleteProject():
    """
    删除项目
    :return:成功返回None,失败返回错误信息(错误码,描述信息)
    """
    try:
        token = request.args.get('token')
        pid = request.args.get('id')
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败/获取id::%s" % e

    if uid:
        try:
            the_project = ItemTeam.query.filter(ItemTeam.id == pid).first()
            if uid != the_project.master_id:
                return 400, "不是该项目的发起者"
            all_teammates = Teammates.query.filter(Teammates.item_id == pid).all()
            all_message = Message.query.filter(Message.project_id == pid).all()
        except Exception as e:
            return 500, "服务器查询对象失败::%s" % e

        try:
            for i in all_teammates:
                db.session.delete(i)
            for i in all_message:
                db.session.delete(i)

            db.session.commit()
            db.session.delete(the_project)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库提交失败::%s" % e

        return None

    else:
        return 400, "token错误"


def DeleteShare():
    """
    删除分享
    :return:成功返回None,失败返回错误信息(错误码,描述信息)
    """
    try:
        token = request.args.get('token')
        pid = request.args.get('id')
        uid = identify(token)
    except Exception as e:
        return 500, "服务器解析token失败/获取id::%s" % e

    if uid:
        try:
            the_share = Share.query.filter(Share.id == pid).first()
            if uid != the_share.uid:
                return 400, "不是该项目的发起者"
            db.session.delete(the_share)
            db.session.commit()
        except Exception as e:
            return 500, "服务器数据库提交失败::%s" % e

        return None

    else:
        return 400, "token错误"


def identify(token):
    """
    鉴别token
    :param token: token
    :return: 成功，返回UID；失败返回False
    """
    cookies = token
    if not cookies:
        return False  # token为空
    datas = cookies.split('/')
    if len(datas) != 3:
        return False  # 假的token

    the_time = datas[1]
    if str(datetime.now()) > the_time:
        return False  # 过期
    the_id = int(datas[0])
    sh = datas[2]

    try:
        result = users.query.filter(users.id == the_id).first()
        calc_key = sha1(datas[0] + result.passwd + the_time + _secret_key)
    except Exception as e:
        # 数据库查询出错/无该id记录
        logging.exception(e)
        return False

    if sh == calc_key:
        return the_id
    else:
        return False  # 假的token


def CheckPassword(username, password):
    """
    检验用户名和密码
    :param username: 用户名
    :param password: 密码
    :return:成功，返回(token,uid),失败返回(False,None)
    """
    the_user = users.query.filter(users.name == username).first()
    if the_user is None:
        return False, None
    if the_user.passwd == password:
        the_id = str(the_user.id)
        the_time = str(datetime.now() + timedelta(days=3))
        the_secret_key = sha1(the_id + password + the_time + _secret_key)
        return the_id + '/' + the_time + '/' + the_secret_key, the_id
    else:
        return False, None


def related(key, obj):
    """
    判别该项目是否与key关联,视情况定义
    :param key:关键字
    :param obj:项目
    :return:
    """
    if key in obj.title or key in obj.types:
        return True
    else:
        return False


def sha1(string):
    a = _sha1()
    a.update(string.encode('utf-8'))
    return a.hexdigest()


def test():
    try:
        print(None)
        print(type(request.form['test']))
    except Exception as e:
        print(e)
