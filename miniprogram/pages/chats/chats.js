const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    chats: [],
  },

  onShow() {
    app.ensureUser(user => {
      if (user.auth_status !== 'approved') return
      this.load()
    })
  },

  load() {
    api.get('/chats', true).then(res => {
      this.setData({ chats: res.data || [] })
    }).catch(() => {})
  },

  goChat(e) {
    wx.navigateTo({ url: '/pages/chat/chat?id=' + e.currentTarget.dataset.id })
  },
})
