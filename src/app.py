import json
from tables import app
from flask import request
from util import GetUserInfo, GetRate, GetFollows, GetResume, GetProject, GetChat, GetJoin, GetResponseJoin,\
    GetHistoryProject, GetProjectTheme, GetFollowers, GetSearchUsers, GetBrowseHistory, GetCountNewMsg,\
    GetBlack, GetShare, GetSearchShares, GetUserShares
from util import DoRate, DoRegister, DoLogin, DoProjectTheme, DoFollow, DoProjectTeam, DoResume, DoChat, DoJoin, \
    DoResponseJoin, DoFinishProject, DoReject, DoUpload, DoCheck, DoShare
from util import ModifyResume, DeleteProject, ModifyInfo, ModifyPassword, DeleteShare
ok_json = json.dumps({"status": 200, "msg": 'ok'})

# ensure_ascii=False


# 上传图片
@app.route('/img/<the_type>', methods=['POST'])
def UploadImage(the_type):
    support_types = ['avatar', 'acticity', 'feedback', 'share']
    if the_type in support_types:
        result, error = DoUpload(the_type)
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        return json.dumps({"status": 400, "msg": '暂不支持其他图片的上传'})


# 登录
@app.route('/user/login', methods=['POST'])
def login():
    result, error = DoLogin()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 获取用户信息/注册
@app.route('/user/info', methods=['GET', 'POST', 'PUT'])
def info():
    if request.method == 'GET':
        result, error = GetUserInfo()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    elif request.method == 'PUT':
        error = ModifyInfo()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json
    else:
        error = DoRegister()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 修改密码
@app.route('/user/password', methods=['PUT'])
def modifyPasswd():
    error = ModifyPassword()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return ok_json


# 上传简历/获取简历
@app.route('/user/resume', methods=['GET', 'POST', 'PUT'])
def resume():
    if request.method == 'GET':
        result, error = GetResume()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    if request.method == 'PUT':
        error = ModifyResume()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json
    else:
        error = DoResume()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 添加评分，获得评分
@app.route('/user/rate', methods=['GET', 'POST'])
def rate():
    if request.method == 'GET':
        result, error = GetRate()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DoRate()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 关注/取消关注
@app.route('/user/follow', methods=['GET', 'POST'])
def follow():
    if request.method == 'GET':
        # 获取uid所有关注的用户
        result, error = GetFollows()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        # 进行关注/取消关注操作
        error = DoFollow()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 获取粉丝
@app.route('/user/follower')
def follower():
    # 获取uid所有粉丝
    result, error = GetFollowers()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 搜索用户
@app.route('/user/search')
def searchUser():
    result, error = GetSearchUsers()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 搜索分享
@app.route('/share/search')
def searchShare():
    result, error = GetSearchShares()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 发私信/获取私信
@app.route('/user/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        result, error = GetChat()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DoChat()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 获得某个用户参加过的组队
@app.route('/project/user')
def historyProject():
    result, error = GetHistoryProject()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 获得某个用户浏览历史
@app.route('/project/history')
def historyUser():
    result, error = GetBrowseHistory()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 获取组队/发布组队
@app.route('/project', methods=['GET', 'POST', 'DELETE'])
def project():
    if request.method == 'GET':
        # 获取发布
        result, error = GetProject()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return result
    if request.method == 'POST':
        # 发布内容
        result, error = DoProjectTeam()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DeleteProject()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 结束组队
@app.route('/project/finish', methods=['POST'])
def overProject():
    error = DoFinishProject()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return ok_json


# 申请组队/获得申请信息
@app.route('/message/join', methods=['GET', 'POST'])
def teamup():
    if request.method == 'GET':
        result, error = GetJoin()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DoJoin()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 回应组队/获得回应消息
@app.route('/message/joinResponse', methods=['GET', 'POST'])
def responseJoin():
    if request.method == 'GET':
        result, error = GetResponseJoin()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DoResponseJoin()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 拉黑
@app.route('/message/reject', methods=['GET', 'POST'])
def reject():
    if request.method == 'GET':
        result, error = GetBlack()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DoReject()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 获取新消息数量
@app.route('/message/new')
def getMsgCount():
    result, error = GetCountNewMsg()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 标记已读/未读
@app.route('/message/isChecked', methods=['POST'])
def isChecked():
    error = DoCheck()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return ok_json


# 获取、发布、删除分享
@app.route('/share', methods=['GET', 'POST', 'DELETE'])
def share():
    if request.method == 'GET':
        result, error = GetShare()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    elif request.method == 'POST':
        result, error = DoShare()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)
    else:
        error = DeleteShare()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return ok_json


# 获取用户所有分享
@app.route('/share/user')
def userShareAll():
    result, error = GetUserShares()
    if error:
        return json.dumps({"status": error[0], "msg": error[1]})
    else:
        return json.dumps(result)


# 发布主题项目
@app.route('/projectTheme', methods=['GET', 'POST'])
def projectTheme():
    if request.method == 'GET':
        result, error = GetProjectTheme()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return result
    else:
        result, error = DoProjectTheme()
        if error:
            return json.dumps({"status": error[0], "msg": error[1]})
        else:
            return json.dumps(result)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
