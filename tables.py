from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@127.0.0.1/web?charset=utf8mb4'
# app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)


# 外键约束供测试用，实际部署去掉


# 用户表
class users(db.Model):
    # 唯一用户id
    id = db.Column(db.Integer, primary_key=True)
    # 用户名
    name = db.Column(db.String(20), unique=True)
    # hash过的密码
    passwd = db.Column(db.String(40))


# 用户信息表
class UsersInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 用户id
    uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 头像url
    avatar = db.Column(db.String(200))
    # 昵称
    nickname = db.Column(db.String(20))
    # 性别
    gender = db.Column(db.String(10))
    # 个性签名,小于100字
    description = db.Column(db.String(100))
    # 学校
    school = db.Column(db.String(100))
    # 校园卡号
    schoolID = db.Column(db.String(40))
    # 专业
    major = db.Column(db.String(30))
    # 入学年份
    grade = db.Column(db.Integer)
    # 兴趣
    interest = db.Column(db.String(100))


# 关注表
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 关注者
    follower = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 被关注者
    befollowed = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 关注时，读取user_info表，复制再存进来，牺牲空间提高性能
    # 被关注者头像路径
    # avatar = db.Column(db.String(200))
    # 被关注者
    # nickname = db.Column(db.String(20))


# 简历表
class CV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 用户id
    uid = db.Column(db.Integer, db.ForeignKey('users.id'))

    # markdown文本
    resume = db.Column(db.Text)

    # 经历
    # experience = db.Column(db.Text)
    # 获奖经历
    # award = db.Column(db.Text)
    # 所学课程
    # course = db.Column(db.Text)
    # 作品
    # works = db.Column(db.Text)
    # 兴趣特长
    # interest = db.Column(db.Text)
    # 个人总结
    # conclude = db.Column(db.Text)


# 个人分享表
class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 用户id
    uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 简介
    brief = db.Column(db.String(100))
    # 内容
    content = db.Column(db.Text)
    # 类别
    category = db.Column(db.String(100))
    # time
    time = db.Column(db.DateTime)


# 他人评价表
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 项目id
    # item_id = db.Column(db.Integer, db.ForeignKey('item_team.id'))
    # 评论者id
    uid1 = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 评论中头像url
    avatar = db.Column(db.String(200))
    # 评论者昵称
    nickname = db.Column(db.String(20))
    # 被评论者id
    uid2 = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 时间
    datetime = db.Column(db.DateTime)
    # 评分等级::态度
    attitude = db.Column(db.Integer)
    # 评分等级::能力
    capability = db.Column(db.Integer)
    # 评分等级::性格
    personality = db.Column(db.Integer)
    # 具体内容
    describe = db.Column(db.Text)
    # 是否已读
    isChecked = db.Column(db.Boolean)


# 项目表
class ItemTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 信息发布者
    master_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 项目名称
    title = db.Column(db.String(30))

    # 项目评级
    rank = db.Column(db.String(30))

    # 是否结束
    finished = db.Column(db.Boolean)

    # 项目tags
    types = db.Column(db.String(100))
    # 项目简介
    describe = db.Column(db.String(200))
    # 发布时间
    publishTime = db.Column(db.DateTime)
    # 开始时间
    begin_date = db.Column(db.Date)

    # 项目周期
    period = db.Column(db.String(100))
    # 结束时间
    # end_time = db.Column(db.DateTime)

    # 组队要求：人数
    req_num = db.Column(db.Integer)
    # 组队要求：年级
    req_mate_grade = db.Column(db.String(100))
    # 组队要求：技能
    req_technique = db.Column(db.String(100))
    # 组队要求：专业
    req_major = db.Column(db.String(100))


# 进行中的项目的队员 表
class Teammates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 用户id
    uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 项目id
    item_id = db.Column(db.Integer, db.ForeignKey('item_team.id'))


# 项目主题表
class ProjectTheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 发布者信息
    publisher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    publisherName = db.Column(db.String(20))
    publisherAvatar = db.Column(db.String(200))
    # 封面图
    cover = db.Column(db.String(200))
    # 简介
    brief = db.Column(db.Text)
    # 内容
    content = db.Column(db.Text)


# 请求信息
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 项目ID
    project_id = db.Column(db.Integer, db.ForeignKey('item_team.id'))
    # 项目标题
    project_title = db.Column(db.String(30))
    # 项目发布者ID
    master_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 申请人ID
    from_uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 留言
    message = db.Column(db.String(200))
    # 回应
    response = db.Column(db.String(200))
    # 是否同意
    state = db.Column(db.Boolean)
    # 请求已读
    isCheck_request = db.Column(db.Boolean)
    # 回复已读
    isCheck_response = db.Column(db.Boolean)
    # 回应时间
    time = db.Column(db.DateTime)


# 私信表
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 发送者uid
    from_uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 发送者昵称
    fromName = db.Column(db.String(20))
    # 发送者头像url
    fromAvatar = db.Column(db.String(200))
    # 接收者uid
    to_uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 详细内容
    message = db.Column(db.String(200))
    # 发送时间
    time = db.Column(db.DateTime)
    # 是否已读
    isChecked = db.Column(db.Boolean)


# 黑名单表
class BlackList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 拉黑者uid
    rejecter = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 被拉黑者uid
    berejecter = db.Column(db.Integer, db.ForeignKey('users.id'))
