// 学搭子小程序入口
const api = require('./utils/api.js')

App({
  globalData: {
    openid: '',
    userInfo: null, // {openid, nickname, avatar, school, auth_status, role}
  },

  onLaunch() {
    // MVP 阶段使用本地持久化的模拟 openid（正式版替换为 wx.login code2session）
    let openid = wx.getStorageSync('openid')
    if (!openid) {
      openid = 'user_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
      wx.setStorageSync('openid', openid)
    }
    this.globalData.openid = openid
    this.refreshUser()
  },

  refreshUser() {
    return api.post('/login', { openid: this.globalData.openid }).then(res => {
      this.globalData.userInfo = res.data
      if (this._userCallbacks) {
        this._userCallbacks.forEach(cb => cb(res.data))
        this._userCallbacks = []
      }
      return res.data
    }).catch(() => null)
  },

  // 页面确保拿到用户信息后再执行回调
  ensureUser(cb) {
    if (this.globalData.userInfo) return cb(this.globalData.userInfo)
    this._userCallbacks = this._userCallbacks || []
    this._userCallbacks.push(cb)
  },

  // 校验是否已选校 + 已认证，否则引导跳转；返回是否可以继续
  checkReady(user, needAuth) {
    if (!user.school) {
      wx.navigateTo({ url: '/pages/school/school' })
      return false
    }
    if (needAuth && user.auth_status !== 'approved') {
      wx.navigateTo({ url: '/pages/verify/verify' })
      return false
    }
    return true
  },
})
